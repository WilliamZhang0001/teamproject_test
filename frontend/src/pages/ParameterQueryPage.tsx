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
  Grid,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Divider,
  FormLabel,
  Checkbox,
  FormGroup,
  FormControlLabel,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography as MuiTypography
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Science as ScienceIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon
} from '@mui/icons-material';
import { experimentService, ExperimentInput, LiteratureRecord } from '../services/experimentService';
import { VALIDATION_RANGES, PARAMETER_HELPER_TEXTS, PARAMETER_LABELS } from '../config/constants';
import { validateParameterValue, getFieldLabel } from '../utils/validators';

const ParameterQueryPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [results, setResults] = useState<any>(null);
  
  // Basic experiment information
  const [biomoleculeType, setBiomoleculeType] = useState('protein');
  const [biomoleculeName, setBiomoleculeName] = useState('');
  const [experimentType, setExperimentType] = useState('stability');
  
  // Optional parameters
  const [pH, setPH] = useState<number | ''>('');
  const [temperature, setTemperature] = useState<number | ''>('');
  const [concentration, setConcentration] = useState<number | ''>('');
  const [ionicStrength, setIonicStrength] = useState<number | ''>('');
  const [additive, setAdditive] = useState('');
  const [time, setTime] = useState<number | ''>('');
  const [shearRate, setShearRate] = useState<number | ''>('');
  const [pressure, setPressure] = useState<number | ''>('');
  
  // Field-level validation errors
  const [fieldErrors, setFieldErrors] = useState<{ [key: string]: string }>({});
  
  // Prediction type and parameter selection
  const [predictionType, setPredictionType] = useState<'classification' | 'parameter'>('classification');
  const [selectedParameters, setSelectedParameters] = useState<string[]>([]);

  const parameterLabels: { [key: string]: string } = {
    pH: 'pH',
    temperature_c: 'Temperature (°C)',
    concentration_mg_ml: 'Concentration (mg/mL)',
    ionic_strength_mM: 'Ionic Strength (mM)',
    additive: 'Additive',
    time_min: 'Time (minutes)',
    shear_rate_s1: 'Shear Rate (s⁻¹)',
    pressure_bar: 'Pressure (bar)'
  };

  // Field validation mapping (frontend field name -> validation range key)
  const fieldToValidationKey: { [key: string]: string } = {
    pH: 'pH',
    temperature: 'temperature_c',
    concentration: 'concentration_mg_ml',
    ionicStrength: 'ionic_strength_mM',
    time: 'time_min',
    shearRate: 'shear_rate_s1',
    pressure: 'pressure_bar'
  };

  // Handle field blur validation
  const handleFieldBlur = (field: string, e?: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const validationKey = fieldToValidationKey[field];
    if (!validationKey) return; // Skip validation for fields without range
    
    // Get current value from the input element or state
    let currentValue: number | string | '';
    if (e && e.target) {
      const inputValue = e.target.value;
      currentValue = inputValue === '' ? '' : (field === 'pH' || field === 'temperature' || field === 'concentration' || field === 'ionicStrength' || field === 'time' || field === 'shearRate' || field === 'pressure' ? Number(inputValue) : inputValue);
    } else {
      // Fallback to state values
      switch (field) {
        case 'pH': currentValue = pH; break;
        case 'temperature': currentValue = temperature; break;
        case 'concentration': currentValue = concentration; break;
        case 'ionicStrength': currentValue = ionicStrength; break;
        case 'time': currentValue = time; break;
        case 'shearRate': currentValue = shearRate; break;
        case 'pressure': currentValue = pressure; break;
        default: return;
      }
    }
    
    const fieldLabel = getFieldLabel(validationKey, PARAMETER_LABELS);
    const errorMsg = validateParameterValue(validationKey, currentValue, VALIDATION_RANGES, fieldLabel);
    if (errorMsg) {
      setFieldErrors(prev => ({
        ...prev,
        [field]: errorMsg
      }));
    } else {
      setFieldErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleParameterToggle = (param: string) => {
    setSelectedParameters(prev =>
      prev.includes(param)
        ? prev.filter(p => p !== param)
        : [...prev, param]
    );
  };

  const handleSubmit = async () => {
    // Validate required fields
    if (!biomoleculeName.trim()) {
      setError('Please enter a biomolecule name');
      return;
    }

    if (!biomoleculeType || !biomoleculeType.trim()) {
      setError('Please select a biomolecule type');
      return;
    }

    if (!experimentType || !experimentType.trim()) {
      setError('Please select an experiment type');
      return;
    }

    if (predictionType === 'parameter' && selectedParameters.length === 0) {
      setError('Please select at least one parameter to predict');
      return;
    }

    setError('');
    setLoading(true);
    setResults(null);

    try {
      const input: ExperimentInput = {
        biomolecule_type: biomoleculeType.trim(),
        biomolecule_name: biomoleculeName.trim(),
        property: experimentType.trim(),
        ...(pH !== '' && { pH: Number(pH) }),
        ...(temperature !== '' && { temperature_c: Number(temperature) }),
        ...(concentration !== '' && { concentration_mg_ml: Number(concentration) }),
        ...(ionicStrength !== '' && { ionic_strength_mM: Number(ionicStrength) }),
        ...(additive !== '' && { additive }),
        ...(time !== '' && { time_min: Number(time) }),
        ...(shearRate !== '' && { shear_rate_s1: Number(shearRate) }),
        ...(pressure !== '' && { pressure_bar: Number(pressure) }),
      };

      let result;
      if (predictionType === 'classification') {
        result = await experimentService.predictClassification(input, 3);
      } else {
        result = await experimentService.predictParameter(input, selectedParameters, 3);
      }
      
      setResults(result);
    } catch (err: any) {
      setError(err.message || 'Prediction failed, please try again');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Parameter Query and Prediction
      </Typography>
      <Typography variant="body1" paragraph color="text.secondary">
        Enter experimental conditions and requirements to get ML model predictions and similar literature references
      </Typography>

      <Paper sx={{ p: 4, mt: 3 }}>
        <Grid container spacing={3}>
          {/* Basic Information */}
          <Grid item xs={12}>
            <Divider sx={{ mb: 3 }}>
              <Typography variant="h6">Basic Information</Typography>
            </Divider>
          </Grid>

          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Biomolecule Type</InputLabel>
              <Select
                value={biomoleculeType}
                label="Biomolecule Type"
                onChange={(e) => setBiomoleculeType(e.target.value)}
              >
                <MenuItem value="protein">Protein</MenuItem>
                <MenuItem value="peptide">Peptide</MenuItem>
                <MenuItem value="polysaccharide">Polysaccharide</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              required
              label="Biomolecule Name"
              placeholder="e.g., lysozyme"
              value={biomoleculeName}
              onChange={(e) => setBiomoleculeName(e.target.value)}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Experiment Type</InputLabel>
              <Select
                value={experimentType}
                label="Experiment Type"
                onChange={(e) => setExperimentType(e.target.value)}
              >
                <MenuItem value="stability">Stability</MenuItem>
                <MenuItem value="solubility">Solubility</MenuItem>
                <MenuItem value="aggregation">Aggregation</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Optional Parameters */}
          <Grid item xs={12}>
            <Divider sx={{ my: 3 }}>
              <Typography variant="h6">Optional Parameters (Known Conditions)</Typography>
            </Divider>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="pH"
              value={pH}
              onChange={(e) => {
                setPH(e.target.value === '' ? '' : Number(e.target.value));
                // Clear error when user starts typing
                if (fieldErrors.pH) {
                  setFieldErrors(prev => {
                    const newErrors = { ...prev };
                    delete newErrors.pH;
                    return newErrors;
                  });
                }
              }}
              onBlur={(e) => handleFieldBlur('pH', e)}
              error={!!fieldErrors.pH}
              helperText={fieldErrors.pH || PARAMETER_HELPER_TEXTS.pH}
              inputProps={{ 
                min: VALIDATION_RANGES.pH.min, 
                max: VALIDATION_RANGES.pH.max, 
                step: VALIDATION_RANGES.pH.step 
              }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Temperature (°C)"
              value={temperature}
              onChange={(e) => {
                setTemperature(e.target.value === '' ? '' : Number(e.target.value));
                if (fieldErrors.temperature) {
                  setFieldErrors(prev => {
                    const newErrors = { ...prev };
                    delete newErrors.temperature;
                    return newErrors;
                  });
                }
              }}
              onBlur={(e) => handleFieldBlur('temperature', e)}
              error={!!fieldErrors.temperature}
              helperText={fieldErrors.temperature || PARAMETER_HELPER_TEXTS.temperature_c}
              inputProps={{ 
                min: VALIDATION_RANGES.temperature_c.min, 
                max: VALIDATION_RANGES.temperature_c.max 
              }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Concentration (mg/mL)"
              value={concentration}
              onChange={(e) => {
                setConcentration(e.target.value === '' ? '' : Number(e.target.value));
                if (fieldErrors.concentration) {
                  setFieldErrors(prev => {
                    const newErrors = { ...prev };
                    delete newErrors.concentration;
                    return newErrors;
                  });
                }
              }}
              onBlur={(e) => handleFieldBlur('concentration', e)}
              error={!!fieldErrors.concentration}
              helperText={fieldErrors.concentration || PARAMETER_HELPER_TEXTS.concentration_mg_ml}
              inputProps={{ 
                min: VALIDATION_RANGES.concentration_mg_ml.min, 
                max: VALIDATION_RANGES.concentration_mg_ml.max,
                step: 0.001
              }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Ionic Strength (mM)"
              value={ionicStrength}
              onChange={(e) => {
                setIonicStrength(e.target.value === '' ? '' : Number(e.target.value));
                if (fieldErrors.ionicStrength) {
                  setFieldErrors(prev => {
                    const newErrors = { ...prev };
                    delete newErrors.ionicStrength;
                    return newErrors;
                  });
                }
              }}
              onBlur={(e) => handleFieldBlur('ionicStrength', e)}
              error={!!fieldErrors.ionicStrength}
              helperText={fieldErrors.ionicStrength || PARAMETER_HELPER_TEXTS.ionic_strength_mM}
              inputProps={{ 
                min: VALIDATION_RANGES.ionic_strength_mM.min, 
                max: VALIDATION_RANGES.ionic_strength_mM.max 
              }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Additive"
              value={additive}
              onChange={(e) => setAdditive(e.target.value)}
              placeholder="e.g., sucrose, glycerol"
              helperText={PARAMETER_HELPER_TEXTS.additive}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Time (minutes)"
              value={time}
              onChange={(e) => {
                setTime(e.target.value === '' ? '' : Number(e.target.value));
                if (fieldErrors.time) {
                  setFieldErrors(prev => {
                    const newErrors = { ...prev };
                    delete newErrors.time;
                    return newErrors;
                  });
                }
              }}
              onBlur={(e) => handleFieldBlur('time', e)}
              error={!!fieldErrors.time}
              helperText={fieldErrors.time || PARAMETER_HELPER_TEXTS.time_min}
              inputProps={{ 
                min: VALIDATION_RANGES.time_min.min, 
                max: VALIDATION_RANGES.time_min.max 
              }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Shear Rate (s⁻¹)"
              value={shearRate}
              onChange={(e) => {
                setShearRate(e.target.value === '' ? '' : Number(e.target.value));
                if (fieldErrors.shearRate) {
                  setFieldErrors(prev => {
                    const newErrors = { ...prev };
                    delete newErrors.shearRate;
                    return newErrors;
                  });
                }
              }}
              onBlur={(e) => handleFieldBlur('shearRate', e)}
              error={!!fieldErrors.shearRate}
              helperText={fieldErrors.shearRate || PARAMETER_HELPER_TEXTS.shear_rate_s1}
              inputProps={{ 
                min: VALIDATION_RANGES.shear_rate_s1.min, 
                max: VALIDATION_RANGES.shear_rate_s1.max 
              }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Pressure (bar)"
              value={pressure}
              onChange={(e) => {
                setPressure(e.target.value === '' ? '' : Number(e.target.value));
                if (fieldErrors.pressure) {
                  setFieldErrors(prev => {
                    const newErrors = { ...prev };
                    delete newErrors.pressure;
                    return newErrors;
                  });
                }
              }}
              onBlur={(e) => handleFieldBlur('pressure', e)}
              error={!!fieldErrors.pressure}
              helperText={fieldErrors.pressure || PARAMETER_HELPER_TEXTS.pressure_bar}
              inputProps={{ 
                min: VALIDATION_RANGES.pressure_bar.min, 
                max: VALIDATION_RANGES.pressure_bar.max 
              }}
            />
          </Grid>

          {/* Prediction Type Selection */}
          <Grid item xs={12}>
            <Divider sx={{ my: 3 }}>
              <Typography variant="h6">Prediction Type</Typography>
            </Divider>
          </Grid>

          <Grid item xs={12}>
            <FormControl component="fieldset">
              <FormGroup row>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={predictionType === 'classification'}
                      onChange={() => setPredictionType('classification')}
                    />
                  }
                  label="Classification (Evaluate experimental conditions)"
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={predictionType === 'parameter'}
                      onChange={() => setPredictionType('parameter')}
                    />
                  }
                  label="Parameter Prediction (Recommend parameter values)"
                />
              </FormGroup>
            </FormControl>
          </Grid>

          {/* Parameter Selection (Parameter Prediction Mode) */}
          {predictionType === 'parameter' && (
            <Grid item xs={12}>
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                <FormLabel component="legend">Select parameters to predict (multiple selection)</FormLabel>
                <FormGroup row sx={{ mt: 2 }}>
                  {Object.keys(parameterLabels).map(param => (
                    <FormControlLabel
                      key={param}
                      control={
                        <Checkbox
                          checked={selectedParameters.includes(param)}
                          onChange={() => handleParameterToggle(param)}
                        />
                      }
                      label={parameterLabels[param]}
                    />
                  ))}
                </FormGroup>
              </Paper>
            </Grid>
          )}

          {/* Error Message */}
          {error && (
            <Grid item xs={12}>
              <Alert 
                severity="error"
                sx={{ whiteSpace: 'pre-line' }}
              >
                {error}
              </Alert>
            </Grid>
          )}

          {/* Submit Button */}
          <Grid item xs={12}>
            <Button
              variant="contained"
              size="large"
              onClick={handleSubmit}
              disabled={loading || !biomoleculeName.trim()}
              startIcon={loading ? <CircularProgress size={20} /> : <ScienceIcon />}
              sx={{ mt: 2 }}
              fullWidth
            >
              {loading ? 'Predicting...' : 'Start Prediction'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Results Display */}
      {results && (
        <Paper sx={{ p: 4, mt: 3 }}>
          <Typography variant="h5" component="h2" gutterBottom>
            Prediction Results
          </Typography>

          {/* Classification Prediction Results */}
          {predictionType === 'classification' && results.data?.prediction && (
            <Card sx={{ mb: 3, bgcolor: results.data.prediction === 'Good' ? 'success.light' : 'error.light' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  {results.data.prediction === 'Good' ? (
                    <CheckCircleIcon sx={{ fontSize: 40, color: 'success.main' }} />
                  ) : (
                    <CancelIcon sx={{ fontSize: 40, color: 'error.main' }} />
                  )}
                  <Box>
                    <MuiTypography variant="h6">
                      Prediction: {results.data.prediction === 'Good' ? 'Good' : 'Bad'}
                    </MuiTypography>
                    <MuiTypography variant="body1" color="text.secondary">
                      Confidence: {(results.data.confidence * 100).toFixed(1)}%
                    </MuiTypography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Parameter Prediction Results */}
          {predictionType === 'parameter' && results.data?.predicted_parameters && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>Predicted Parameter Values</Typography>
              
              {/* Display provided parameters as separate alert message */}
              {Object.entries(results.data.predicted_parameters).map(([param, value]: [string, any]) => {
                // Check if parameter is already provided (special key for multiple provided params)
                if (param === '_provided_params' && value.status === 'already_provided') {
                  const providedParams = value.provided_params || [];
                  const providedValues = value.provided_values || {};
                  
                  return (
                    <Alert 
                      key="provided_params_alert" 
                      severity="info" 
                      sx={{ mb: 2 }}
                    >
                      <Typography variant="body1" sx={{ fontWeight: 'bold', mb: 1 }}>
                        {value.message || 'Parameters already provided'}
                      </Typography>
                      <Box component="div" sx={{ mt: 1 }}>
                        {providedParams.map((p: string, idx: number) => {
                          const val = providedValues[p];
                          const displayVal = typeof val === 'number' 
                            ? val.toFixed(2) 
                            : (val || 'N/A');
                          return (
                            <Typography key={p} variant="body2" component="span">
                              {parameterLabels[p] || p}: <strong>{displayVal}</strong>
                              {idx < providedParams.length - 1 ? ', ' : ''}
                            </Typography>
                          );
                        })}
                      </Box>
                    </Alert>
                  );
                }
                
                // Check if single parameter is already provided (backward compatibility)
                if (value.status === 'already_provided' && param !== '_provided_params') {
                  return (
                    <Alert 
                      key={`${param}_alert`} 
                      severity="info" 
                      sx={{ mb: 2 }}
                    >
                      <Typography variant="body1" sx={{ fontWeight: 'bold', mb: 1 }}>
                        {value.message || `${param} already provided`}
                      </Typography>
                      <Typography variant="body2">
                        {parameterLabels[param] || param}: <strong>
                          {typeof value.provided_value === 'number' 
                            ? value.provided_value.toFixed(2) 
                            : value.provided_value || 'N/A'}
                        </strong>
                      </Typography>
                    </Alert>
                  );
                }
                
                return null;
              })}
              
              {/* Display predicted parameters in table */}
              {Object.entries(results.data.predicted_parameters).some(([param, value]: [string, any]) => 
                param !== '_provided_params' && value.status !== 'already_provided'
              ) && (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Parameter</TableCell>
                        <TableCell align="right">Recommended Value</TableCell>
                        <TableCell align="right">Common Values / Min</TableCell>
                        <TableCell align="right">Count / Max</TableCell>
                        <TableCell align="right">Usage / Median</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(results.data.predicted_parameters)
                        .filter(([param, value]: [string, any]) => 
                          param !== '_provided_params' && value.status !== 'already_provided'
                        )
                        .map(([param, value]: [string, any]) => {
                          // Parameter needs prediction
                          const isStringParam = value.is_string || typeof value.recommended_value === 'string';
                          
                          return (
                            <TableRow key={param}>
                              <TableCell>{parameterLabels[param] || param}</TableCell>
                              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                                {isStringParam ? (
                                  value.recommended_value || 'N/A'
                                ) : (
                                  typeof value.recommended_value === 'number' 
                                    ? value.recommended_value.toFixed(2) 
                                    : value.recommended_value || 'N/A'
                                )}
                              </TableCell>
                              <TableCell align="right">
                                {isStringParam ? (
                                  value.common_values && value.common_values.length > 0
                                    ? value.common_values.slice(0, 3).join(', ')
                                    : 'N/A'
                                ) : (
                                  typeof value.min === 'number' ? value.min.toFixed(2) : (value.min || 'N/A')
                                )}
                              </TableCell>
                              <TableCell align="right">
                                {isStringParam ? (
                                  value.count ? `${value.count} occurrences` : 'N/A'
                                ) : (
                                  typeof value.max === 'number' ? value.max.toFixed(2) : (value.max || 'N/A')
                                )}
                              </TableCell>
                              <TableCell align="right">
                                {isStringParam ? (
                                  value.top_count ? `Used ${value.top_count} times` : 'N/A'
                                ) : (
                                  typeof value.median === 'number' ? value.median.toFixed(2) : (value.median || 'N/A')
                                )}
                              </TableCell>
                            </TableRow>
                          );
                        })}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
              <Chip
                label={`Overall Confidence: ${(results.data.confidence * 100).toFixed(1)}%`}
                color="primary"
                sx={{ mt: 2 }}
              />
            </Box>
          )}

          {/* Similar Literature */}
          {results.data?.similar_literature && results.data.similar_literature.length > 0 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Similar Literature References ({results.data.similar_literature.length})
              </Typography>
              {results.data.similar_literature.map((lit: LiteratureRecord, idx: number) => {
                // Get literature metadata (support both top-level and nested structure)
                const title = lit.title || lit.literature?.title;
                const authors = lit.authors || lit.literature?.authors;
                const pubYear = lit.pub_year || lit.literature?.pub_year;
                const doi = lit.doi || lit.literature?.doi;
                
                return (
                  <Accordion key={lit.id || idx} sx={{ mt: 1 }}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box sx={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', pr: 1 }}>
                        <Box sx={{ flex: 1, minWidth: 0 }}>
                          <Typography 
                            variant="subtitle1" 
                            sx={{ 
                              fontWeight: 600,
                              color: 'primary.main',
                              mb: 0.5,
                              wordBreak: 'break-word',
                              overflowWrap: 'break-word',
                              hyphens: 'auto',
                              display: '-webkit-box',
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: 'vertical',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis'
                            }}
                          >
                            {title || `Literature Record #${lit.id}`}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {authors && pubYear
                              ? `${authors} • ${pubYear}`
                              : authors
                              ? authors
                              : pubYear
                              ? `Year: ${pubYear}`
                              : 'No metadata available'}
                          </Typography>
                        </Box>
                        <Chip
                          label={`Similarity: ${(lit.similarity_score * 100).toFixed(1)}%`}
                          color="primary"
                          size="small"
                          sx={{ ml: 2, flexShrink: 0 }}
                        />
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Box>
                        {/* Literature Metadata Section */}
                        {(authors || pubYear || doi) && (
                          <Box 
                            sx={{ 
                              mb: 2, 
                              p: 1.5, 
                              bgcolor: 'grey.50', 
                              borderRadius: 1, 
                              border: '1px solid', 
                              borderColor: 'grey.200' 
                            }}
                          >
                            <Grid container spacing={1.5}>
                              {authors && (
                                <Grid item xs={12} sm={pubYear || doi ? 6 : 12}>
                                  <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
                                    <Typography 
                                      variant="caption" 
                                      sx={{ 
                                        fontWeight: 'bold', 
                                        color: 'text.secondary',
                                        minWidth: '60px',
                                        mr: 1
                                      }}
                                    >
                                      Authors:
                                    </Typography>
                                    <Typography 
                                      variant="body2" 
                                      sx={{ 
                                        color: 'text.primary',
                                        wordBreak: 'break-word'
                                      }}
                                    >
                                      {authors}
                                    </Typography>
                                  </Box>
                                </Grid>
                              )}
                              {pubYear && (
                                <Grid item xs={12} sm={authors && doi ? 3 : 6}>
                                  <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
                                    <Typography 
                                      variant="caption" 
                                      sx={{ 
                                        fontWeight: 'bold', 
                                        color: 'text.secondary',
                                        minWidth: '50px',
                                        mr: 1
                                      }}
                                    >
                                      Year:
                                    </Typography>
                                    <Typography variant="body2" color="text.primary">
                                      {pubYear}
                                    </Typography>
                                  </Box>
                                </Grid>
                              )}
                              {doi && (
                                <Grid item xs={12} sm={authors && pubYear ? 3 : authors || pubYear ? 6 : 12}>
                                  <Box sx={{ display: 'flex', alignItems: 'flex-start', flexWrap: 'wrap' }}>
                                    <Typography 
                                      variant="caption" 
                                      sx={{ 
                                        fontWeight: 'bold', 
                                        color: 'text.secondary',
                                        minWidth: '45px',
                                        mr: 1
                                      }}
                                    >
                                      DOI:
                                    </Typography>
                                    <Typography 
                                      variant="body2" 
                                      component="a"
                                      href={doi.startsWith('http') ? doi : `https://doi.org/${doi}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      sx={{ 
                                        color: 'primary.main',
                                        textDecoration: 'none',
                                        '&:hover': {
                                          textDecoration: 'underline'
                                        },
                                        wordBreak: 'break-word'
                                      }}
                                    >
                                      {doi}
                                    </Typography>
                                  </Box>
                                </Grid>
                              )}
                            </Grid>
                          </Box>
                        )}
                      {lit.parameters && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                            Experimental Parameters:
                          </Typography>
                          <TableContainer>
                            <Table size="small" sx={{ '& .MuiTableCell-root': { borderBottom: '1px solid rgba(224, 224, 224, 0.5)' } }}>
                              <TableBody>
                                {Object.entries(lit.parameters)
                                  .filter(([key, value]) => key !== 'raw_context' && value !== null && value !== undefined && value !== '')
                                  .map(([key, value]) => {
                                    const paramLabel = PARAMETER_LABELS[key] || key;
                                    let displayValue = value;
                                    if (typeof value === 'number') {
                                      displayValue = value.toLocaleString('en-US', { 
                                        maximumFractionDigits: 6,
                                        useGrouping: false 
                                      });
                                    } else if (typeof value === 'string' && value.length > 100) {
                                      displayValue = value.substring(0, 100) + '...';
                                    }
                                    return (
                                      <TableRow key={key}>
                                        <TableCell sx={{ fontWeight: 'bold', width: '40%', verticalAlign: 'top' }}>
                                          {paramLabel}
                                        </TableCell>
                                        <TableCell sx={{ verticalAlign: 'top' }}>
                                          {String(displayValue)}
                                        </TableCell>
                                      </TableRow>
                                    );
                                  })}
                              </TableBody>
                            </Table>
                          </TableContainer>
                          {lit.parameters.raw_context && (
                            <Box sx={{ mt: 1, p: 1.5, bgcolor: 'grey.50', borderRadius: 1, border: '1px solid', borderColor: 'grey.300' }}>
                              <Typography variant="caption" sx={{ fontWeight: 'bold', display: 'block', mb: 0.5, color: 'text.secondary' }}>
                                Context:
                              </Typography>
                              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                                {lit.parameters.raw_context}
                              </Typography>
                            </Box>
                          )}
                        </Box>
                      )}
                      {lit.outcome_text && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                            Experimental Results:
                          </Typography>
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                            {lit.outcome_text}
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  </AccordionDetails>
                </Accordion>
              );
              })}
            </Box>
          )}
        </Paper>
      )}
    </Box>
  );
};

export default ParameterQueryPage;

