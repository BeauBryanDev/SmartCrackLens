import { useState, useEffect } from 'react';
import { locationService } from '../services/locationService';
import { Location } from '../types';


export const useLocationsDropdown = () => {
    
  const [locations, setLocations] = useState<Location[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);


  useEffect(() => {

    const fetchLocations = async () => {

      try {

        // Fetching the first page with a high limit to get all typical locations for the dropdown
        const response = await locationService.listLocations(1, 50);
        setLocations(response.results ?? []);
      } catch (error) {
        console.error('[HUD_SYSTEM]: Failed to load location dictionaries.', error);
        setLocations([]);
      } finally {

        setIsLoading(false);
      }
    };

    fetchLocations();

  }, []);

  return { locations, isLoading };

};
