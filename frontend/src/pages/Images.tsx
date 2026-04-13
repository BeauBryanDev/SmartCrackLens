import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileImage, MapPin, Layers, Eye, Trash2, RefreshCcw, Database, ScanSearch } from 'lucide-react';
import axios from 'axios';
import { imageService } from '../services/imageService';
import { useLocationsDropdown } from '../hooks/useLocationsDropDown';
import { SURFACE_TYPES } from '../utils/constants';
import { CyberButton } from '../components/CyberButton';
import { ImageDoc, Location, UploadInferenceResponse } from '../types';


export const Images: React.FC = () => {
  // Use custom hook to get the locations seamlessly
  const navigate = useNavigate();

  const { locations, isLoading: isLoadingLocations } = useLocationsDropdown();

  // Form State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [surfaceType, setSurfaceType] = useState<string>(SURFACE_TYPES[0].id);
  const [locationId, setLocationId] = useState<string>('');

  // Upload State
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [latestUpload, setLatestUpload] = useState<UploadInferenceResponse | null>(null);
  const [images, setImages] = useState<ImageDoc[]>([]);
  const [isLoadingImages, setIsLoadingImages] = useState<boolean>(true);
  const [imageMessage, setImageMessage] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<ImageDoc | null>(null);
  const [selectedOutputSrc, setSelectedOutputSrc] = useState<string | null>(null);
  const [isLoadingOutput, setIsLoadingOutput] = useState<boolean>(false);
  const [editingLocations, setEditingLocations] = useState<Record<string, string>>({});
  const [busyImageId, setBusyImageId] = useState<string | null>(null);

  useEffect(() => {
    void loadImages();
  }, []);

  useEffect(() => {
    return () => {
      if (selectedOutputSrc?.startsWith('blob:')) {
        URL.revokeObjectURL(selectedOutputSrc);
      }
    };
  }, [selectedOutputSrc]);

  const loadImages = async () => {
    try {
      setIsLoadingImages(true);
      const response = await imageService.listImages({ page: 1, pageSize: 24 });
      setImages(response.results ?? []);
      setEditingLocations(
        Object.fromEntries(
          (response.results ?? []).map((image) => [image.id, image.location_id ?? ''])
        )
      );
    } catch (error) {
      console.error('[HUD_IMAGES_LIST_ERROR]: Failed to load image registry.', error);
      setImageMessage('ERROR: UNABLE_TO_LOAD_IMAGE_REGISTRY');
      setImages([]);
    } finally {
      setIsLoadingImages(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadMessage(null);

    try {

      const response = await imageService.uploadAndAnalyze(
        selectedFile,
        surfaceType,
        locationId === '' ? undefined : locationId
      );

      setLatestUpload(response);

      setUploadMessage('SCAN_UPLOADED_AND_ANALYZED_SUCCESSFULLY');
      setSelectedFile(null);
      setLocationId('');
      setImageMessage('IMAGE_REGISTRY_UPDATED');
      await loadImages();


    } catch (error) {

      console.error('[HUD_UPLOAD_ERROR]: Inference pipeline failed.', error);
      setLatestUpload(null);

      if (axios.isAxiosError(error)) {

        const detail = error.response?.data?.detail;

        if (typeof detail === 'string') {

          setUploadMessage(`ERROR: ${detail}`);

        } else if (Array.isArray(detail)) {

          setUploadMessage(`ERROR: ${detail.map((item) => item.msg).join(' | ')}`);

        } else {

          setUploadMessage('ERROR: UPLOAD_FAILED_OR_REJECTED_BY_SERVER');
        }
      } else {

        setUploadMessage('ERROR: UPLOAD_FAILED_OR_REJECTED_BY_SERVER');
      }
    } finally {

      setIsUploading(false);
    }
  };

  const outputPreviewSrc = latestUpload?.output_image_b64
    ? `data:image/jpeg;base64,${latestUpload.output_image_b64}`
    : null;
  const completedImages = images.filter((image) => image.inference_status === 'completed').length;
  const assignedImages = images.filter((image) => image.location_id).length;
  const totalCracksInRegistry = images.reduce((sum, image) => sum + image.total_cracks_detected, 0);

  const getLocationLabel = (targetLocationId?: string) => {
    if (!targetLocationId) return 'UNASSIGNED_LOCATION';
    const match = locations.find((location) => location.id === targetLocationId);
    return match ? `${match.name} / ${match.city}` : 'UNKNOWN_LOCATION';
  };

  const handleLoadImageDetails = async (imageId: string) => {
    try {
      setBusyImageId(imageId);
      const image = await imageService.getImageById(imageId);
      setSelectedImage(image);
      setImageMessage(`DETAIL_LINKED: ${image.original_filename}`);
    } catch (error) {
      console.error('[HUD_IMAGE_DETAIL_ERROR]: Failed to fetch image detail.', error);
      setImageMessage('ERROR: DETAIL_REQUEST_FAILED');
    } finally {
      setBusyImageId(null);
    }
  };

  const handlePreviewOutput = async (imageId: string) => {
    try {
      setBusyImageId(imageId);
      setIsLoadingOutput(true);
      const blob = await imageService.getOutputImageBlob(imageId);
      const objectUrl = URL.createObjectURL(blob);
      setSelectedOutputSrc((current) => {
        if (current?.startsWith('blob:')) {
          URL.revokeObjectURL(current);
        }
        return objectUrl;
      });

      const image = selectedImage?.id === imageId
        ? selectedImage
        : await imageService.getImageById(imageId);
      setSelectedImage(image);
      setImageMessage(`OUTPUT_STREAM_READY: ${image.original_filename}`);
    } catch (error) {
      console.error('[HUD_IMAGE_OUTPUT_ERROR]: Failed to stream output image.', error);
      setImageMessage('ERROR: OUTPUT_STREAM_UNAVAILABLE');
    } finally {
      setBusyImageId(null);
      setIsLoadingOutput(false);
    }
  };

  const handlePatchLocation = async (imageId: string) => {
    try {
      setBusyImageId(imageId);
      const nextLocationId = editingLocations[imageId] || null;
      const updatedImage = await imageService.patchImage(imageId, { location_id: nextLocationId });
      setImages((current) =>
        current.map((image) => (image.id === imageId ? { ...image, ...updatedImage } : image))
      );
      setSelectedImage((current) => (current?.id === imageId ? { ...current, ...updatedImage } : current));
      setImageMessage('LOCATION_ASSOCIATION_UPDATED');
    } catch (error) {
      console.error('[HUD_IMAGE_PATCH_ERROR]: Failed to update image location.', error);
      setImageMessage('ERROR: LOCATION_PATCH_FAILED');
    } finally {
      setBusyImageId(null);
    }
  };

  const handleDeleteImage = async (imageId: string) => {
    try {
      setBusyImageId(imageId);
      const response = await imageService.deleteImage(imageId);
      setImages((current) => current.filter((image) => image.id !== imageId));
      setEditingLocations((current) => {
        const next = { ...current };
        delete next[imageId];
        return next;
      });

      if (selectedImage?.id === imageId) {
        setSelectedImage(null);
      }
      setSelectedOutputSrc((current) => {
        if (current?.startsWith('blob:')) {
          URL.revokeObjectURL(current);
        }
        return null;
      });

      setImageMessage(`IMAGE_PURGED: ${response.deleted_id}`);
    } catch (error) {
      console.error('[HUD_IMAGE_DELETE_ERROR]: Failed to delete image.', error);
      setImageMessage('ERROR: IMAGE_DELETE_FAILED');
    } finally {
      setBusyImageId(null);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">

      <div className="border-b border-crack-neon/30 pb-4">
        <h1 className="text-2xl font-orbitron font-bold text-white tracking-widest uppercase">
          Structural <span className="text-crack-cyan">Scans</span>
        </h1>
        <p className="text-crack-cyan/60 font-mono text-xs mt-1">
          UPLOAD RAW IMAGES TO TRIGGER ONNX INFERENCE ENGINE
        </p>
      </div>

      {/* UPLOAD CONSOLE */}
      <div className="border border-crack-electric/50 bg-crack-deep/30 p-6 relative">
        <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none"></div>

        <h2 className="text-sm font-mono text-crack-cyan tracking-widest mb-6 flex items-center gap-2">
          <Upload className="w-4 h-4" />
          NEW_SCAN_ENTRY
        </h2>

        {uploadMessage && (
          <div className="mb-4 p-3 border border-crack-cyan/50 bg-crack-cyan/10 text-crack-cyan font-mono text-xs">
            {uploadMessage}
          </div>
        )}

        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 relative z-10">

          {/* FILE INPUT */}
          <div className="lg:col-span-2 space-y-2">
            <label className="text-[10px] font-mono text-crack-cyan/70 tracking-widest uppercase flex items-center gap-2">
              <FileImage className="w-3 h-3" /> Image_Binary (JPEG/PNG/WEBP)
            </label>
            <input
              type="file"
              accept="image/jpeg, image/png, image/webp"
              onChange={handleFileChange}
              required
              className="w-full bg-crack-dark border border-crack-electric/50 p-2 text-white font-mono text-sm file:mr-4 file:py-2 file:px-4 file:rounded-none file:border-0 file:text-sm file:font-orbitron file:bg-crack-cyan/20 file:text-crack-cyan hover:file:bg-crack-cyan/30 transition-all cursor-pointer"
            />
          </div>

          {/* SURFACE TYPE SELECT */}
          <div className="space-y-2">
            <label className="text-[10px] font-mono text-crack-cyan/70 tracking-widest uppercase flex items-center gap-2">
              <Layers className="w-3 h-3" /> Surface_Material
            </label>
            <select
              value={surfaceType}
              onChange={(e) => setSurfaceType(e.target.value)}
              className="w-full bg-crack-dark border border-crack-electric/50 p-3 text-white font-mono text-sm focus:outline-none focus:border-crack-neon appearance-none cursor-pointer"
            >
              {SURFACE_TYPES.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* LOCATION SELECT */}
          <div className="space-y-2">
            <label className="text-[10px] font-mono text-crack-cyan/70 tracking-widest uppercase flex items-center gap-2">
              <MapPin className="w-3 h-3" /> Spatial_Coordinates
            </label>
            <select
              value={locationId}
              onChange={(e) => setLocationId(e.target.value)}
              disabled={isLoadingLocations}
              className="w-full bg-crack-dark border border-crack-electric/50 p-3 text-white font-mono text-sm focus:outline-none focus:border-crack-neon appearance-none cursor-pointer disabled:opacity-50"
            >
              <option value="">[ UNASSIGNED_LOCATION ]</option>
              {locations.map((loc: Location) => (
                // Backend gets the 'loc.id' (UUID), user sees the 'loc.name'
                <option key={loc.id} value={loc.id}>
                  {loc.name}
                </option>
              ))}
            </select>
          </div>

          <div className="lg:col-span-4 flex justify-end mt-2">
            <CyberButton
              type="submit"
              disabled={!selectedFile || isUploading}
              isLoading={isUploading}
            >
              EXECUTE_PIPELINE
            </CyberButton>
          </div>

        </form>
      </div>

      {latestUpload && (
        <div className="grid grid-cols-1 xl:grid-cols-[1.4fr_0.8fr] gap-6">
          <div className="border border-crack-electric/50 bg-crack-deep/30 p-6 relative">
            <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none"></div>
            <h2 className="text-sm font-mono text-crack-cyan tracking-widest mb-4">
              PROCESSED_OUTPUT
            </h2>

            {outputPreviewSrc ? (
              <img
                src={outputPreviewSrc}
                alt={`Processed inference output for ${latestUpload.image.original_filename}`}
                className="w-full max-h-[32rem] object-contain border border-crack-electric/40 bg-black/30"
              />
            ) : (
              <div className="min-h-[18rem] border border-crack-electric/30 bg-crack-dark/60 flex items-center justify-center text-center px-6">
                <p className="text-crack-cyan/70 font-mono text-xs tracking-widest">
                  NO_ANNOTATED_OUTPUT_GENERATED. THE MODEL DID NOT DRAW A MASK FOR THIS SCAN.
                </p>
              </div>
            )}
          </div>

          <div className="border border-crack-electric/50 bg-crack-deep/30 p-6 relative">
            <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none"></div>
            <h2 className="text-sm font-mono text-crack-cyan tracking-widest mb-4">
              PIPELINE_RESULT
            </h2>

            <div className="space-y-4 text-sm font-mono relative z-10">
              <div className="border border-crack-electric/30 bg-crack-dark/50 p-4">
                <p className="text-crack-cyan/60 text-[10px] tracking-widest mb-1">FILENAME</p>
                <p className="text-white break-all">{latestUpload.image.original_filename}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <MetricPanel
                  label="CRACKS"
                  value={latestUpload.detection.total_cracks}
                />
                <MetricPanel
                  label="LATENCY"
                  value={`${latestUpload.detection.inference_ms} ms`}
                />
                <MetricPanel
                  label="STATUS"
                  value={latestUpload.image.inference_status}
                />
                <MetricPanel
                  label="SURFACE"
                  value={latestUpload.detection.surface_type}
                />
              </div>

              <div className="border border-crack-electric/30 bg-crack-dark/50 p-4">
                <p className="text-crack-cyan/60 text-[10px] tracking-widest mb-2">ACCESS_LINK</p>
                <a
                  href={latestUpload.output_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-crack-cyan hover:text-crack-neon break-all"
                >
                  {latestUpload.output_url}
                </a>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[1.35fr_0.65fr] gap-6">
        <div className="border border-crack-electric/50 bg-[linear-gradient(180deg,rgba(3,4,94,0.72),rgba(1,19,36,0.94))] p-6 relative overflow-hidden">
          <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none"></div>
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(0,180,216,0.12),transparent_34%),radial-gradient(circle_at_bottom_right,rgba(0,119,182,0.12),transparent_32%)] pointer-events-none"></div>
          <div className="flex flex-col gap-4 mb-5 relative z-10">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-sm font-mono text-crack-cyan tracking-[0.28em] flex items-center gap-2">
                  <Database className="w-4 h-4" />
                  IMAGE_OPERATION_BOARD
                </h2>
                <p className="text-crack-cyan/60 font-mono text-[10px] mt-2 tracking-[0.18em] uppercase">
                  patch routing, stream output, inspect signals, purge stored scans
                </p>
              </div>
              <CyberButton
                type="button"
                onClick={() => void loadImages()}
                disabled={isLoadingImages}
              >
                <RefreshCcw className="w-4 h-4" />
                REFRESH
              </CyberButton>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <RegistryChip label="REGISTRY_SIZE" value={images.length} />
              <RegistryChip label="COMPLETED" value={completedImages} />
              <RegistryChip label="CRACK_TOTAL" value={totalCracksInRegistry} />
            </div>
          </div>

          {imageMessage && (
            <div className="mb-4 p-3 border border-crack-cyan/40 bg-crack-cyan/10 text-crack-cyan font-mono text-xs tracking-[0.16em] relative z-10">
              {imageMessage}
            </div>
          )}

          {isLoadingImages ? (
            <div className="min-h-[18rem] flex items-center justify-center text-crack-cyan font-mono text-xs tracking-widest relative z-10">
              SYNCING_IMAGE_REGISTRY...
            </div>
          ) : images.length === 0 ? (
            <div className="min-h-[18rem] border border-crack-electric/30 bg-crack-dark/60 flex items-center justify-center text-center px-6 relative z-10">
              <p className="text-crack-cyan/70 font-mono text-xs tracking-widest">
                NO_IMAGES_REGISTERED. EXECUTE THE PIPELINE TO BUILD YOUR IMAGE HISTORY.
              </p>
            </div>
          ) : (
            <div className="space-y-4 relative z-10">
              {images.map((image) => (
                <div
                  key={image.id}
                  className="group relative overflow-hidden border border-crack-electric/35 bg-[linear-gradient(135deg,rgba(1,22,39,0.94),rgba(3,4,94,0.58))] p-4 md:p-5 grid grid-cols-1 lg:grid-cols-[1.18fr_0.82fr] gap-4 shadow-[0_0_0_1px_rgba(0,180,216,0.08),0_16px_36px_rgba(0,0,0,0.28)] transition-colors duration-300 hover:border-crack-cyan/55"
                >
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-[linear-gradient(90deg,transparent,rgba(144,224,239,0.05),transparent)] pointer-events-none"></div>
                  <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-crack-cyan/80 to-transparent opacity-60"></div>

                  <div className="space-y-4">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-white font-orbitron tracking-[0.14em] break-all text-sm md:text-base">
                          {image.original_filename}
                        </p>
                        <p className="text-crack-cyan/55 font-mono text-[10px] mt-2 tracking-[0.16em]">
                          SIGNAL_ID // {image.id}
                        </p>
                      </div>
                      <StatusPill status={image.inference_status} />
                    </div>

                    <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
                      <MetricPanel label="CRACKS" value={image.total_cracks_detected} />
                      <MetricPanel label="LATENCY" value={image.inference_ms ? `${image.inference_ms} ms` : 'N/A'} />
                      <MetricPanel label="ASSIGNED" value={image.location_id ? 'YES' : 'NO'} />
                      <MetricPanel label="UPLOADED" value={new Date(image.uploaded_at).toLocaleDateString()} />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-3 items-end">
                      <div className="border border-crack-electric/30 bg-black/20 p-3">
                        <p className="text-crack-cyan/60 font-mono text-[10px] tracking-[0.18em] mb-2">
                          LOCATION_ROUTING
                        </p>
                        <select
                          value={editingLocations[image.id] ?? image.location_id ?? ''}
                          onChange={(event) =>
                            setEditingLocations((current) => ({
                              ...current,
                              [image.id]: event.target.value,
                            }))
                          }
                          disabled={isLoadingLocations || busyImageId === image.id}
                          className="w-full bg-crack-dark border border-crack-electric/50 p-3 text-white font-mono text-sm focus:outline-none focus:border-crack-neon appearance-none cursor-pointer disabled:opacity-50"
                        >
                          <option value="">[ UNASSIGNED_LOCATION ]</option>
                          {locations.map((loc) => (
                            <option key={loc.id} value={loc.id}>
                              {loc.name} / {loc.city}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="border border-crack-electric/25 bg-crack-dark/40 p-3 min-w-[12rem]">
                        <p className="text-crack-cyan/60 font-mono text-[10px] tracking-[0.18em] mb-2">
                          ACTIVE_LINK
                        </p>
                        <p className="text-white font-mono text-xs leading-relaxed">
                          {getLocationLabel(editingLocations[image.id] || image.location_id)}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="border border-crack-electric/25 bg-black/20 p-3">
                      <p className="text-crack-cyan/60 font-mono text-[10px] tracking-[0.18em] mb-3">
                        COMMAND_RAIL
                      </p>
                      <div className="grid grid-cols-2 gap-3">
                        <CyberButton
                          type="button"
                          onClick={() => void handlePatchLocation(image.id)}
                          disabled={busyImageId === image.id}
                        >
                          <MapPin className="w-4 h-4" />
                          PATCH
                        </CyberButton>
                        <CyberButton
                          type="button"
                          onClick={() => navigate(`/inference/${image.id}`)}
                          disabled={busyImageId === image.id}
                        >
                          <ScanSearch className="w-4 h-4" />
                          INSPECT
                        </CyberButton>
                        <CyberButton
                          type="button"
                          onClick={() => void handlePreviewOutput(image.id)}
                          disabled={busyImageId === image.id || image.inference_status !== 'completed'}
                        >
                          <Eye className="w-4 h-4" />
                          OUTPUT
                        </CyberButton>
                        <CyberButton
                          type="button"
                          onClick={() => void handleDeleteImage(image.id)}
                          disabled={busyImageId === image.id}
                        >
                          <Trash2 className="w-4 h-4" />
                          PURGE
                        </CyberButton>
                      </div>
                    </div>

                    <div className="border border-crack-electric/25 bg-black/20 p-3">
                      <p className="text-crack-cyan/60 font-mono text-[10px] tracking-[0.18em] mb-3">
                        SIGNAL_TRACE
                      </p>
                      <div className="space-y-3">
                        <SignalLine label="stored" value={image.stored_filename} />
                        <SignalLine label="dimensions" value={image.width_px && image.height_px ? `${image.width_px}x${image.height_px}` : 'N/A'} />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="border border-crack-electric/50 bg-[linear-gradient(180deg,rgba(3,4,94,0.72),rgba(1,19,36,0.94))] p-6 relative overflow-hidden">
            <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none"></div>
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(144,224,239,0.08),transparent_38%)] pointer-events-none"></div>
            <h2 className="text-sm font-mono text-crack-cyan tracking-[0.28em] mb-4 relative z-10">
              IMAGE_INSPECTOR
            </h2>

            {selectedImage ? (
              <div className="space-y-3 relative z-10">
                <MetricPanel label="FILENAME" value={selectedImage.original_filename} />
                <MetricPanel label="LOCATION" value={getLocationLabel(selectedImage.location_id)} />
                <MetricPanel label="STORED_NAME" value={selectedImage.stored_filename} />
                <MetricPanel label="MIME" value={selectedImage.mime_type ?? 'N/A'} />
                <MetricPanel label="SIZE" value={selectedImage.size_bytes ? `${Math.round(selectedImage.size_bytes / 1024)} KB` : 'N/A'} />
                <MetricPanel label="DIMENSIONS" value={selectedImage.width_px && selectedImage.height_px ? `${selectedImage.width_px}x${selectedImage.height_px}` : 'N/A'} />
              </div>
            ) : (
              <div className="min-h-[16rem] border border-crack-electric/30 bg-crack-dark/60 flex items-center justify-center text-center px-6 relative z-10">
                <p className="text-crack-cyan/70 font-mono text-xs tracking-widest">
                  SELECT AN IMAGE RECORD TO LOAD ITS FULL DOCUMENT DETAILS.
                </p>
              </div>
            )}
          </div>

          <div className="border border-crack-electric/50 bg-[linear-gradient(180deg,rgba(3,4,94,0.72),rgba(1,19,36,0.94))] p-6 relative overflow-hidden">
            <div className="absolute inset-0 bg-scanline opacity-10 pointer-events-none"></div>
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_right,rgba(0,119,182,0.1),transparent_42%)] pointer-events-none"></div>
            <h2 className="text-sm font-mono text-crack-cyan tracking-[0.28em] mb-4 relative z-10">
              OUTPUT_INSPECTOR
            </h2>

            {isLoadingOutput ? (
              <div className="min-h-[18rem] flex items-center justify-center text-crack-cyan font-mono text-xs tracking-widest relative z-10">
                STREAMING_ANNOTATED_OUTPUT...
              </div>
            ) : selectedOutputSrc ? (
              <img
                src={selectedOutputSrc}
                alt="Stored processed output"
                className="w-full max-h-[28rem] object-contain border border-crack-electric/40 bg-black/30 relative z-10"
              />
            ) : (
              <div className="min-h-[18rem] border border-crack-electric/30 bg-crack-dark/60 flex items-center justify-center text-center px-6 relative z-10">
                <p className="text-crack-cyan/70 font-mono text-xs tracking-widest">
                  LOAD A COMPLETED IMAGE OUTPUT TO REVIEW THE STORED SEGMENTATION MASK.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

    </div>
  );
};

const MetricPanel = ({ label, value }: { label: string; value: string | number }) => (
  <div className="border border-crack-electric/30 bg-crack-dark/50 p-4">
    <p className="text-crack-cyan/60 text-[10px] tracking-widest mb-1">{label}</p>
    <p className="text-white text-lg font-orbitron tracking-wide uppercase">{value}</p>
  </div>
);

const RegistryChip = ({ label, value }: { label: string; value: string | number }) => (
  <div className="border border-crack-electric/30 bg-[linear-gradient(180deg,rgba(0,180,216,0.08),rgba(1,22,39,0.55))] px-4 py-3">
    <p className="text-crack-cyan/60 text-[10px] font-mono tracking-[0.2em] mb-1">{label}</p>
    <p className="text-white text-xl font-orbitron tracking-[0.14em]">{value}</p>
  </div>
);

const SignalLine = ({ label, value }: { label: string; value: string }) => (
  <div className="border border-crack-electric/20 bg-crack-dark/40 px-3 py-2">
    <p className="text-crack-cyan/55 text-[10px] font-mono tracking-[0.18em] mb-1 uppercase">{label}</p>
    <p className="text-white text-xs font-mono break-all">{value}</p>
  </div>
);

const StatusPill = ({ status }: { status: string }) => {
  const tone =
    status === 'completed'
      ? 'border-crack-cyan/50 text-crack-neon bg-crack-cyan/10'
      : status === 'failed'
        ? 'border-red-400/50 text-red-300 bg-red-500/10'
        : 'border-amber-400/50 text-amber-200 bg-amber-400/10';

  return (
    <span className={`px-3 py-1 text-[10px] font-mono tracking-[0.2em] border uppercase ${tone}`}>
      {status}
    </span>
  );
};

export default Images;
