import React from 'react';
import { Box, Typography, Paper, Alert } from '@mui/material';

const DataInputPage: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Manual Data Input
      </Typography>
      <Typography variant="body1" paragraph color="text.secondary">
        Input your experimental data to help improve our machine learning models.
      </Typography>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Alert severity="info">
          This page is under development. The manual data input interface will be implemented here.
        </Alert>
        
        <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
          Planned Features:
        </Typography>
        <ul>
          <li>Form-based data entry</li>
          <li>CSV/Excel file upload</li>
          <li>Data validation</li>
          <li>Batch data import</li>
        </ul>
      </Paper>
    </Box>
  );
};

export default DataInputPage;

