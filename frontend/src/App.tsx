import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';


import { ProtectedRoute } from './components/ProtectedRoute';
import { PublicLayout } from  './layouts/PublicLayout';
import { HudLayout } from './layouts/HUDLayout';

// -- Public Pages --
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';

// -- Protected HUD Pages --
import MainDashboard from './pages/MainDashboard';
import Images from './pages/Images';
import Inference from './pages/Inference';
import Detections from './pages/Detections';
import Locations from './pages/Locations';
import Profile from './pages/Profile';

export const App = () => {

  return (
    
    <BrowserRouter>
      <Routes>
        {/*  PUBLIC ZONE */}
        {/* Imagine these are wrapped inside a <Route element={<PublicLayout />}> */}
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />

        {/* COMMAND CENTER (PROTECTED ZONE)  */}
        <Route element={<ProtectedRoute />}>
          {/* Imagine these are wrapped inside a <Route element={<HudLayout />}> */}
          <Route path="/dashboard" element={<MainDashboard />} />
          <Route path="/images" element={<Images />} />
          <Route path="/inference/:imageId?" element={<Inference />} />
          <Route path="/detections" element={<Detections />} />
          <Route path="/locations" element={<Locations />} />
          <Route path="/me" element={<Profile />} />
        </Route>

        {/* Catch-all route: Redirect unknown URLs to the landing page */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;