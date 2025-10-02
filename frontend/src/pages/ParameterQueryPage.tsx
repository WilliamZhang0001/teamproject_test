import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Button, 
  Paper,
  TextField,
  Grid
} from '@mui/material';

const ParameterQueryPage: React.FC = () => {
  const [experimentType, setExperimentType] = useState('');
  const [constraints, setConstraints] = useState({
    temperatureMin: '',
    temperatureMax: '',
    pressureMin: '',
    pressureMax: ''
  });

  const handleSubmit = () => {
    // TODO: Implement parameter query logic
    console.log('Querying parameters for:', experimentType, constraints);
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Parameter Query
      </Typography>
      <Typography variant="body1" paragraph color="text.secondary">
        Specify your experiment type and constraints to get optimal parameter recommendations.
      </Typography>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Experiment Type</InputLabel>
              <Select
                value={experimentType}
                label="Experiment Type"
                onChange={(e) => setExperimentType(e.target.value)}
              >
                <MenuItem value="solubility">Solubility Study</MenuItem>
                <MenuItem value="crystallization">Crystallization</MenuItem>
                <MenuItem value="reaction">Chemical Reaction</MenuItem>
                <MenuItem value="extraction">Extraction</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Temperature Range (°C)"
              placeholder="e.g., 20-80"
              value={`${constraints.temperatureMin}-${constraints.temperatureMax}`}
              onChange={(e) => {
                const [min, max] = e.target.value.split('-');
                setConstraints(prev => ({
                  ...prev,
                  temperatureMin: min || '',
                  temperatureMax: max || ''
                }));
              }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Pressure Range (atm)"
              placeholder="e.g., 1-5"
              value={`${constraints.pressureMin}-${constraints.pressureMax}`}
              onChange={(e) => {
                const [min, max] = e.target.value.split('-');
                setConstraints(prev => ({
                  ...prev,
                  pressureMin: min || '',
                  pressureMax: max || ''
                }));
              }}
            />
          </Grid>

          <Grid item xs={12}>
            <Button
              variant="contained"
              size="large"
              onClick={handleSubmit}
              disabled={!experimentType}
              sx={{ mt: 2 }}
            >
              Get Parameter Recommendations
            </Button>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default ParameterQueryPage;

