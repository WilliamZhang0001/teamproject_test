import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  Button,
  Alert,
  LinearProgress,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Card,
  CardContent,
  Chip,
  Link,
  TextField,
  FormGroup,
  FormControlLabel,
  Checkbox
} from '@mui/material';
import { CloudUpload, Download, CheckCircle, Error as ErrorIcon } from '@mui/icons-material';
import { experimentService } from '../services/experimentService';
import { PARAMETER_LABELS } from '../config/constants';

const AVAILABLE_PARAMETERS = [
  'pH',
  'temperature_c',
  'concentration_mg_ml',
  'ionic_strength_mM',
  'time_min',
  'shear_rate_s1',
  'pressure_bar',
  'additive'
];

const UploadDatasetPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState(false);
  const [predictionType, setPredictionType] = useState<'classification' | 'parameter'>('classification');
  const [selectedParameters, setSelectedParameters] = useState<string[]>([]);
  const [topK, setTopK] = useState<number>(3);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [downloadFilename, setDownloadFilename] = useState<string>('');

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.csv')) {
        setError('Only CSV file format is supported');
        return;
      }
      setSelectedFile(file);
      setError('');
      setSuccess(false);
      setDownloadUrl(null);
    }
  };

  const handleParameterToggle = (param: string) => {
    setSelectedParameters(prev => 
      prev.includes(param)
        ? prev.filter(p => p !== param)
        : [...prev, param]
    );
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    // Validate parameter selection for parameter prediction type
    if (predictionType === 'parameter' && selectedParameters.length === 0) {
      setError('Please select at least one parameter to predict');
      return;
    }

    setError('');
    setSuccess(false);
    setUploading(true);

    try {
      const predictParams = predictionType === 'parameter' ? selectedParameters : undefined;
      const blob = await experimentService.predictCSV(
        selectedFile,
        predictionType,
        topK,
        predictParams
      );
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      setDownloadUrl(url);
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      setDownloadFilename(`predictions_${timestamp}.csv`);
      setSuccess(true);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Batch prediction failed, please check file format';
      setError(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = () => {
    if (downloadUrl) {
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = downloadFilename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setError('');
    setSuccess(false);
    setDownloadUrl(null);
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        CSV Batch Prediction
      </Typography>
      <Typography variant="body1" paragraph color="text.secondary">
        Upload CSV file for batch experimental prediction analysis
      </Typography>

      <Paper sx={{ p: 4, mt: 3 }}>
        <Grid container spacing={3}>
          {/* Prediction Type Selection */}
          <Grid item xs={12}>
            <Divider sx={{ mb: 3 }}>
              <Typography variant="h6">Prediction Type</Typography>
            </Divider>
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Prediction Method</InputLabel>
              <Select
                value={predictionType}
                label="Prediction Method"
                onChange={(e) => {
                  const newType = e.target.value as 'classification' | 'parameter';
                  setPredictionType(newType);
                  if (newType === 'classification') {
                    setSelectedParameters([]);
                  }
                }}
              >
                <MenuItem value="classification">Classification</MenuItem>
                <MenuItem value="parameter">Parameter Prediction</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Top K Literature (Number of similar literature)"
              type="number"
              value={topK}
              onChange={(e) => setTopK(Math.max(1, parseInt(e.target.value) || 3))}
              inputProps={{ min: 1, max: 10 }}
              helperText="Number of similar literature records to include (1-10)"
            />
          </Grid>

          {predictionType === 'parameter' && (
            <Grid item xs={12}>
              <Card variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold', mb: 2 }}>
                  Select Parameters to Predict:
                </Typography>
                <FormGroup>
                  <Grid container spacing={2}>
                    {AVAILABLE_PARAMETERS.map((param) => (
                      <Grid item xs={6} sm={4} md={3} key={param}>
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={selectedParameters.includes(param)}
                              onChange={() => handleParameterToggle(param)}
                            />
                          }
                          label={PARAMETER_LABELS[param] || param}
                        />
                      </Grid>
                    ))}
                  </Grid>
                  {selectedParameters.length === 0 && (
                    <Alert severity="warning" sx={{ mt: 2 }}>
                      Please select at least one parameter to predict
                    </Alert>
                  )}
                </FormGroup>
              </Card>
            </Grid>
          )}

          {/* File Upload */}
          <Grid item xs={12}>
            <Divider sx={{ my: 3 }}>
              <Typography variant="h6">File Upload</Typography>
            </Divider>
          </Grid>

          <Grid item xs={12}>
            <Box
              sx={{
                border: '2px dashed',
                borderColor: selectedFile ? 'primary.main' : 'grey.300',
                borderRadius: 2,
                p: 3,
                textAlign: 'center',
                bgcolor: selectedFile ? 'primary.light' : 'grey.50',
                transition: 'all 0.3s'
              }}
            >
              {selectedFile ? (
                <Box>
                  <CheckCircle sx={{ fontSize: 48, color: 'success.main', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    {selectedFile.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    File Size: {(selectedFile.size / 1024).toFixed(2)} KB
                  </Typography>
                  <Button
                    variant="outlined"
                    onClick={handleRemoveFile}
                    sx={{ mt: 2 }}
                  >
                    Remove File
                  </Button>
                </Box>
              ) : (
                <Box>
                  <CloudUpload sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
                  <Typography variant="body1" gutterBottom>
                    Select CSV file to upload
                  </Typography>
                  <input
                    accept=".csv"
                    style={{ display: 'none' }}
                    id="csv-upload"
                    type="file"
                    onChange={handleFileSelect}
                    disabled={uploading}
                  />
                  <label htmlFor="csv-upload">
                    <Button
                      variant="contained"
                      component="span"
                      startIcon={<CloudUpload />}
                      disabled={uploading}
                      sx={{ mt: 2 }}
                    >
                      Select File
                    </Button>
                  </label>
                </Box>
              )}
            </Box>
          </Grid>

          {/* File Format Instructions */}
          <Grid item xs={12}>
            <Card variant="outlined" sx={{ bgcolor: 'info.light', p: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                <strong>CSV File Format Requirements:</strong>
              </Typography>
              <Typography variant="body2" component="div">
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  <li>Must include header row</li>
                  <li>Required columns (must be filled, values must be lowercase): Substance Category, Substance Name, Property</li>
                  <li>Supported values: Substance Category (protein, peptide, polysaccharide), Property (stability, solubility, aggregation)</li>
                  <li>Optional columns: pH, Temperature, Concentration, Ion Concentration, Additives, Time, Shear Rate, Pressure</li>
                  <li>All numeric values should be in number format</li>
                </ul>
              </Typography>
            </Card>
          </Grid>

          {/* Error Message */}
          {error && (
            <Grid item xs={12}>
              <Alert severity="error" icon={<ErrorIcon />}>
                {error}
              </Alert>
            </Grid>
          )}

          {/* Success Message */}
          {success && (
            <Grid item xs={12}>
              <Alert severity="success" icon={<CheckCircle />}>
                Prediction completed! Click the download button below to get results
              </Alert>
            </Grid>
          )}

          {/* Upload Progress */}
          {uploading && (
            <Grid item xs={12}>
              <Box sx={{ width: '100%', mt: 2 }}>
                <LinearProgress />
                <Typography variant="body2" sx={{ mt: 1 }} align="center">
                  Processing file, please wait...
                </Typography>
              </Box>
            </Grid>
          )}

          {/* Action Buttons */}
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                onClick={handleUpload}
                disabled={!selectedFile || uploading}
                startIcon={<CloudUpload />}
                fullWidth
              >
                {uploading ? 'Processing...' : 'Start Batch Prediction'}
              </Button>
              {success && downloadUrl && (
                <Button
                  variant="outlined"
                  onClick={handleDownload}
                  startIcon={<Download />}
                  fullWidth
                >
                  Download Results
                </Button>
              )}
            </Box>
          </Grid>

          {/* Example Format */}
          <Grid item xs={12}>
            <Divider sx={{ my: 3 }}>
              <Typography variant="body2" color="text.secondary">
                Need Help?
              </Typography>
            </Divider>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Please refer to the requirements or contact technical support
              </Typography>
              <Chip
                label="Please enter the parameters in the order specified by the requirements; each line represents one experiment."
                sx={{ mt: 1 }}
              />
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default UploadDatasetPage;
