import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';

interface LoadingProps {
  message?: string;
  fullScreen?: boolean;
  size?: number;
}

const Loading: React.FC<LoadingProps> = ({ 
  message = 'Loading...', 
  fullScreen = false,
  size = 40
}) => {
  const content = (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      sx={fullScreen ? {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        bgcolor: 'rgba(255, 255, 255, 0.8)',
        zIndex: 9999
      } : {
        py: 4
      }}
    >
      <CircularProgress size={size} />
      {message && (
        <Typography variant="body1" sx={{ mt: 2, color: 'text.secondary' }}>
          {message}
        </Typography>
      )}
    </Box>
  );

  return content;
};

export default Loading;

