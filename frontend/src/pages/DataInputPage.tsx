import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Alert,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Divider,
  Chip,
  CircularProgress,
  Card,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CardContent
} from '@mui/material';
import { Search as SearchIcon, CheckCircle as CheckCircleIcon } from '@mui/icons-material';
import { experimentService, LiteratureRecord } from '../services/experimentService';
import { VALIDATION_RANGES, PARAMETER_HELPER_TEXTS, PARAMETER_LABELS } from '../config/constants';
import { validateParameterValue, getFieldLabel } from '../utils/validators';

const DataInputPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [results, setResults] = useState<LiteratureRecord[]>([]);
  const [searchCount, setSearchCount] = useState(0);
  
  // Search criteria
  const [biomoleculeName, setBiomoleculeName] = useState('');
  const [propertyType, setPropertyType] = useState('stability');
  const [pH, setPH] = useState<number | ''>('');
  const [temperature, setTemperature] = useState<number | ''>('');
  const [concentration, setConcentration] = useState<number | ''>('');
  const [ionicStrength, setIonicStrength] = useState<number | ''>('');
  const [additive, setAdditive] = useState('');
  const [time, setTime] = useState<number | ''>('');
  const [shearRate, setShearRate] = useState<number | ''>('');
  const [pressure, setPressure] = useState<number | ''>('');
  const [limit, setLimit] = useState(5);
  
  // Field-level validation errors
  const [fieldErrors, setFieldErrors] = useState<{ [key: string]: string }>({});

  const handleSearch = async () => {
    if (!biomoleculeName.trim()) {
      setError('Please enter a biomolecule name');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const results = await experimentService.searchLiterature(
        {
          biomolecule_name: biomoleculeName,
          property: propertyType,
          pH: pH !== '' ? Number(pH) : undefined,
          temperature_c: temperature !== '' ? Number(temperature) : undefined,
          concentration_mg_ml: concentration !== '' ? Number(concentration) : undefined,
          ionic_strength_mM: ionicStrength !== '' ? Number(ionicStrength) : undefined,
          additive: additive !== '' ? additive : undefined,
          time_min: time !== '' ? Number(time) : undefined,
          shear_rate_s1: shearRate !== '' ? Number(shearRate) : undefined,
          pressure_bar: pressure !== '' ? Number(pressure) : undefined,
        },
        limit
      );
      
      setResults(results);
      setSearchCount(prev => prev + 1);
    } catch (err: any) {
      setError(err.message || 'Literature search failed');
    } finally {
      setLoading(false);
    }
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

  const handleClear = () => {
    setBiomoleculeName('');
    setPH('');
    setTemperature('');
    setConcentration('');
    setIonicStrength('');
    setAdditive('');
    setTime('');
    setShearRate('');
    setPressure('');
    setResults([]);
    setError('');
    setSearchCount(0);
    setFieldErrors({});
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Literature Search
      </Typography>
      <Typography variant="body1" paragraph color="text.secondary">
        Search for similar literature based on experimental conditions to get reference data
      </Typography>

      <Paper sx={{ p: 4, mt: 3 }}>
        <Grid container spacing={3}>
          {/* Basic Information */}
          <Grid item xs={12}>
            <Divider sx={{ mb: 3 }}>
              <Typography variant="h6">Search Criteria</Typography>
            </Divider>
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
              <InputLabel>Property Type</InputLabel>
              <Select
                value={propertyType}
                label="Property Type"
                onChange={(e) => setPropertyType(e.target.value)}
              >
                <MenuItem value="stability">Stability</MenuItem>
                <MenuItem value="solubility">Solubility</MenuItem>
                <MenuItem value="aggregation">Aggregation</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Number of Results</InputLabel>
              <Select
                value={limit}
                label="Number of Results"
                onChange={(e) => setLimit(Number(e.target.value))}
              >
                <MenuItem value={3}>3</MenuItem>
                <MenuItem value={5}>5</MenuItem>
                <MenuItem value={10}>10</MenuItem>
                <MenuItem value={20}>20</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* Optional Filter Conditions */}
          <Grid item xs={12}>
            <Divider sx={{ my: 3 }}>
              <Typography variant="body2" color="text.secondary">
                Optional Filter Conditions (can be left empty)
              </Typography>
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

          {/* Action Buttons */}
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                size="large"
                onClick={handleSearch}
                disabled={loading || !biomoleculeName.trim()}
                startIcon={loading ? <CircularProgress size={20} /> : <SearchIcon />}
              >
                {loading ? 'Searching...' : 'Search Literature'}
              </Button>
              <Button
                variant="outlined"
                size="large"
                onClick={handleClear}
                disabled={loading}
              >
                Clear Conditions
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Search Results */}
      {results.length > 0 && (
        <Paper sx={{ p: 4, mt: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5" component="h2">
              Search Results
            </Typography>
            <Chip
              label={`Found ${results.length} similar literature`}
              color="primary"
              icon={<CheckCircleIcon />}
            />
          </Box>

          <Grid container spacing={2}>
            {results.map((lit, idx) => (
              <Grid item xs={12} key={lit.id || idx}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                      <Box sx={{ flex: 1 }}>
                        {lit.literature?.title ? (
                          <Typography variant="h6" gutterBottom>
                            {lit.literature.title}
                          </Typography>
                        ) : (
                          <Typography variant="h6" gutterBottom>
                            Literature Record #{lit.id}
                          </Typography>
                        )}
                        {lit.literature?.authors && (
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            <strong>Authors:</strong> {lit.literature.authors}
                          </Typography>
                        )}
                        {lit.literature?.pub_year && (
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            <strong>Year:</strong> {lit.literature.pub_year}
                          </Typography>
                        )}
                        {lit.literature?.doi && (
                          <Typography variant="body2" color="text.secondary">
                            <strong>DOI:</strong> {lit.literature.doi}
                          </Typography>
                        )}
                        {!lit.literature && (
                          <Typography variant="body2" color="text.secondary">
                            <em>No literature metadata available</em>
                          </Typography>
                        )}
                      </Box>
                      <Chip
                        label={`Similarity: ${(lit.similarity_score * 100).toFixed(1)}%`}
                        color="primary"
                        size="small"
                        sx={{ ml: 2 }}
                      />
                    </Box>

                    {lit.parameters && (
                      <Box sx={{ mt: 2 }}>
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

                    {lit.confidence !== undefined && (
                      <Chip
                        label={`Confidence: ${(lit.confidence * 100).toFixed(1)}%`}
                        color="success"
                        size="small"
                        sx={{ mt: 2 }}
                      />
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Search Hint */}
      {searchCount === 0 && !loading && (
        <Paper sx={{ p: 3, mt: 3, bgcolor: 'info.light' }}>
          <Typography variant="body1" align="center" color="text.secondary">
            Please enter search criteria and click the "Search Literature" button
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default DataInputPage;

