import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Alert,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Divider,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar
} from '@mui/material';
import {
  History as HistoryIcon,
  Visibility as VisibilityIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  ExpandMore as ExpandMoreIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import {
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import { experimentService, ExperimentHistory, LiteratureRecord } from '../services/experimentService';
import { PARAMETER_LABELS } from '../config/constants';

const ResultsDisplayPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [history, setHistory] = useState<ExperimentHistory[]>([]);
  const [selectedExperiment, setSelectedExperiment] = useState<ExperimentHistory | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await experimentService.getHistory(50);
      setHistory(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (id: number) => {
    try {
      const experiment = await experimentService.getExperiment(id);
      
      // Parse JSON strings if needed
      const parsedExperiment = {
        ...experiment,
        prediction_result: typeof experiment.prediction_result === 'string' 
          ? JSON.parse(experiment.prediction_result) 
          : experiment.prediction_result,
        recommended_literature: typeof experiment.recommended_literature === 'string'
          ? JSON.parse(experiment.recommended_literature)
          : Array.isArray(experiment.recommended_literature)
          ? experiment.recommended_literature
          : []
      };
      
      setSelectedExperiment(parsedExperiment);
      setDialogOpen(true);
    } catch (err: any) {
      setError(err.message || 'Failed to load details');
    }
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedExperiment(null);
  };

  // Statistics - Parse prediction_result which may be a JSON string
  const calculateStats = (hist: ExperimentHistory[]) => {
    let goodCount = 0;
    let badCount = 0;
    
    hist.forEach(h => {
      try {
        // Parse prediction_result if it's a string
        const result = typeof h.prediction_result === 'string' 
          ? JSON.parse(h.prediction_result) 
          : h.prediction_result;
        
        // Check both result.prediction and result.data.prediction
        const prediction = result?.prediction || result?.data?.prediction;
        
        if (prediction === 'Good') {
          goodCount++;
        } else if (prediction === 'Bad') {
          badCount++;
        }
      } catch (e) {
        // If parsing fails, skip this record
        console.error('Failed to parse prediction_result for record', h.id, e);
      }
    });
    
    return {
      total: hist.length,
      good: goodCount,
      bad: badCount,
      avgConfidence: hist.length > 0
        ? (hist.reduce((sum, h) => sum + (h.confidence || 0), 0) / hist.length * 100).toFixed(1)
        : '0.0'
    };
  };

  const stats = calculateStats(history);

  const handleDeleteAll = async () => {
    setDeleting(true);
    setError('');
    try {
      const result = await experimentService.deleteHistory();
      setHistory([]);
      setDeleteDialogOpen(false);
      // Show success message using Snackbar
      setSnackbarMessage(`Successfully deleted ${result.deleted_count} experiment record(s)`);
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to delete history';
      setError(errorMsg);
      setSnackbarMessage(errorMsg);
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Experiment History
          </Typography>
          <Typography variant="body1" color="text.secondary">
            View and manage your experimental prediction history
          </Typography>
        </Box>
        {history.length > 0 && (
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={() => setDeleteDialogOpen(true)}
            sx={{ ml: 2 }}
          >
            Clear All Data
          </Button>
        )}
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <HistoryIcon sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                <Box>
                  <Typography variant="h4" color="primary">
                    {stats.total}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Records
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingUpIcon sx={{ fontSize: 40, color: 'success.main', mr: 2 }} />
                <Box>
                  <Typography variant="h4" color="success.main">
                    {stats.good}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Good Predictions
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AssessmentIcon sx={{ fontSize: 40, color: 'error.main', mr: 2 }} />
                <Box>
                  <Typography variant="h4" color="error.main">
                    {stats.bad}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Bad Predictions
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TimelineIcon sx={{ fontSize: 40, color: 'info.main', mr: 2 }} />
                <Box>
                  <Typography variant="h4" color="info.main">
                    {stats.avgConfidence}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Average Confidence
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* History List */}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6">
            Recent Records
          </Typography>
          <Button
            variant="outlined"
            startIcon={<HistoryIcon />}
            onClick={loadHistory}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {!loading && !error && history.length === 0 && (
          <Alert severity="info" sx={{ mb: 3 }}>
            No history records
          </Alert>
        )}

        {!loading && !error && history.length > 0 && (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Biomolecule</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Prediction Type</TableCell>
                  <TableCell>Result</TableCell>
                  <TableCell>Confidence</TableCell>
                  <TableCell>Created At</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {history.map((item) => (
                  <TableRow key={item.id} hover>
                    <TableCell>{item.id}</TableCell>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="bold">
                          {item.biomolecule_name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {item.biomolecule_type}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip label={item.experiment_type} size="small" color="primary" variant="outlined" />
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={item.prediction_type === 'classification' ? 'Classification' : 'Parameter Prediction'} 
                        size="small" 
                        color="secondary" 
                        variant="outlined" 
                      />
                    </TableCell>
                    <TableCell>
                      {(() => {
                        try {
                          const result = typeof item.prediction_result === 'string' 
                            ? JSON.parse(item.prediction_result) 
                            : item.prediction_result;
                          const prediction = result?.prediction || result?.data?.prediction;
                          
                          if (prediction === 'Good' || prediction === 'Bad') {
                            return (
                              <Chip
                                label={prediction}
                                size="small"
                                color={prediction === 'Good' ? 'success' : 'error'}
                              />
                            );
                          }
                          return null;
                        } catch (e) {
                          return null;
                        }
                      })()}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {(item.confidence * 100).toFixed(1)}%
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {new Date(item.created_at).toLocaleString('en-US')}
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => handleViewDetails(item.id)}
                        color="primary"
                      >
                        <VisibilityIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Details Dialog */}
      <Dialog 
        open={dialogOpen} 
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              Experiment Details
            </Typography>
            <IconButton onClick={handleCloseDialog}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedExperiment && (() => {
            // Parse prediction_result
            let predictionResult: any = selectedExperiment.prediction_result;
            if (typeof predictionResult === 'string') {
              try {
                predictionResult = JSON.parse(predictionResult);
              } catch (e) {
                console.error('Failed to parse prediction_result:', e);
                predictionResult = null;
              }
            }

            // Parse recommended_literature
            let literature: LiteratureRecord[] = [];
            if (selectedExperiment.recommended_literature) {
              if (typeof selectedExperiment.recommended_literature === 'string') {
                try {
                  literature = JSON.parse(selectedExperiment.recommended_literature);
                } catch (e) {
                  console.error('Failed to parse recommended_literature:', e);
                  literature = [];
                }
              } else if (Array.isArray(selectedExperiment.recommended_literature)) {
                literature = selectedExperiment.recommended_literature;
              }
            }

            // Determine prediction type and result
            const isClassification = selectedExperiment.prediction_type === 'classification';
            const resultData = predictionResult?.data || predictionResult;
            const prediction = resultData?.prediction;
            const predictedParams = resultData?.predicted_parameters;
            const similarLit = resultData?.similar_literature || literature;

            return (
              <Box>
                {/* Basic Information */}
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Biomolecule Type
                    </Typography>
                    <Typography variant="body1">
                      {selectedExperiment.biomolecule_type}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Biomolecule Name
                    </Typography>
                    <Typography variant="body1" fontWeight="bold">
                      {selectedExperiment.biomolecule_name}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Experiment Type
                    </Typography>
                    <Typography variant="body1">
                      {selectedExperiment.experiment_type}
                    </Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Prediction Type
                    </Typography>
                    <Typography variant="body1">
                      {isClassification ? 'Classification' : 'Parameter Prediction'}
                    </Typography>
                  </Grid>
                </Grid>

                <Divider sx={{ my: 2 }} />

                {/* Classification Prediction Results */}
                {isClassification && prediction && (
                  <Card sx={{ mb: 3, bgcolor: prediction === 'Good' ? 'success.light' : 'error.light' }}>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        {prediction === 'Good' ? (
                          <CheckCircleIcon sx={{ fontSize: 40, color: 'success.main' }} />
                        ) : (
                          <CancelIcon sx={{ fontSize: 40, color: 'error.main' }} />
                        )}
                        <Box>
                          <Typography variant="h6">
                            Prediction: {prediction === 'Good' ? 'Good' : 'Bad'}
                          </Typography>
                          <Typography variant="body1" color="text.secondary">
                            Confidence: {((selectedExperiment.confidence || resultData?.confidence || 0) * 100).toFixed(1)}%
                          </Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                )}

                {/* Parameter Prediction Results */}
                {!isClassification && predictedParams && Object.keys(predictedParams).length > 0 && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h6" gutterBottom>Predicted Parameter Values</Typography>
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
                          {Object.entries(predictedParams).map(([param, value]: [string, any]) => {
                            const isStringParam = value.is_string || typeof value.recommended_value === 'string';
                            
                            return (
                              <TableRow key={param}>
                                <TableCell>{PARAMETER_LABELS[param] || param}</TableCell>
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
                    <Chip
                      label={`Overall Confidence: ${((selectedExperiment.confidence || resultData?.confidence || 0) * 100).toFixed(1)}%`}
                      color="primary"
                      sx={{ mt: 2 }}
                    />
                  </Box>
                )}

                {/* Similar Literature References */}
                {similarLit && similarLit.length > 0 && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Similar Literature References ({similarLit.length})
                    </Typography>
                    {similarLit.map((lit: LiteratureRecord, idx: number) => {
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
              </Box>
            );
          })()}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => !deleting && setDeleteDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <DeleteIcon sx={{ color: 'error.main', mr: 1 }} />
            Confirm Delete All Data
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            Are you sure you want to delete all your experiment records? This action cannot be undone.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            You have {history.length} experiment record(s) that will be permanently deleted.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setDeleteDialogOpen(false)}
            disabled={deleting}
            color="inherit"
          >
            Cancel
          </Button>
          <Button
            onClick={handleDeleteAll}
            disabled={deleting}
            color="error"
            variant="contained"
            startIcon={deleting ? <CircularProgress size={20} /> : <DeleteIcon />}
          >
            {deleting ? 'Deleting...' : 'Delete All'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success/Error Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbarOpen(false)}
          severity={snackbarSeverity}
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ResultsDisplayPage;

