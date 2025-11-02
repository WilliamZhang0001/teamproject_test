import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Alert,
  Grid,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Rating,
  Divider,
  Chip
} from '@mui/material';
import { Send as SendIcon, CheckCircle as CheckCircleIcon } from '@mui/icons-material';

const FeedbackPage: React.FC = () => {
  const [submitted, setSubmitted] = useState(false);
  const [rating, setRating] = useState<number | null>(5);
  const [comments, setComments] = useState('');
  const [experimentType, setExperimentType] = useState('');
  const [satisfaction, setSatisfaction] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Simulate submission
    console.log({ rating, comments, experimentType, satisfaction });
    setSubmitted(true);
    
    // Reset form after 3 seconds
    setTimeout(() => {
      setSubmitted(false);
      setRating(5);
      setComments('');
      setExperimentType('');
      setSatisfaction('');
    }, 3000);
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Submit Feedback
      </Typography>
      <Typography variant="body1" paragraph color="text.secondary">
        Share your experience to help us improve the system
      </Typography>

      {submitted ? (
        <Paper sx={{ p: 4, mt: 3 }}>
          <Alert severity="success" icon={<CheckCircleIcon />}>
            Thank you for your feedback! We will carefully evaluate your suggestions
          </Alert>
        </Paper>
      ) : (
        <Paper sx={{ p: 4, mt: 3 }}>
          <form onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Divider sx={{ mb: 3 }}>
                  <Typography variant="h6">Overall Rating</Typography>
                </Divider>
              </Grid>

              <Grid item xs={12}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Typography variant="body1">
                    Usage Satisfaction:
                  </Typography>
                  <Rating
                    value={rating}
                    onChange={(_, newValue) => setRating(newValue)}
                    size="large"
                  />
                  <Chip 
                    label={rating ? `${rating}/5` : 'Not Rated'} 
                    color="primary"
                    size="small"
                  />
                </Box>
              </Grid>

              <Grid item xs={12}>
                <Divider sx={{ my: 3 }}>
                  <Typography variant="h6">Details</Typography>
                </Divider>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Experiment Type</InputLabel>
                  <Select
                    value={experimentType}
                    label="Experiment Type"
                    onChange={(e) => setExperimentType(e.target.value)}
                  >
                    <MenuItem value="stability">Stability Study</MenuItem>
                    <MenuItem value="solubility">Solubility Study</MenuItem>
                    <MenuItem value="aggregation">Aggregation Study</MenuItem>
                    <MenuItem value="other">Other</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Feature Satisfaction</InputLabel>
                  <Select
                    value={satisfaction}
                    label="Feature Satisfaction"
                    onChange={(e) => setSatisfaction(e.target.value)}
                  >
                    <MenuItem value="very-satisfied">Very Satisfied</MenuItem>
                    <MenuItem value="satisfied">Satisfied</MenuItem>
                    <MenuItem value="neutral">Neutral</MenuItem>
                    <MenuItem value="dissatisfied">Dissatisfied</MenuItem>
                    <MenuItem value="very-dissatisfied">Very Dissatisfied</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={6}
                  label="Detailed Feedback"
                  placeholder="Please describe your experience, issues encountered, or improvement suggestions..."
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                />
              </Grid>

              <Grid item xs={12}>
                <Button
                  type="submit"
                  variant="contained"
                  size="large"
                  startIcon={<SendIcon />}
                  disabled={!rating}
                  fullWidth
                >
                  Submit Feedback
                </Button>
              </Grid>

              <Grid item xs={12}>
                <Divider />
              </Grid>

              <Grid item xs={12}>
                <Alert severity="info">
                  <Typography variant="body2">
                    <strong>Feedback may include:</strong>
                  </Typography>
                  <ul style={{ margin: '8px 0', paddingLeft: '24px' }}>
                    <li>Evaluation of prediction accuracy and usefulness</li>
                    <li>Problems or difficulties encountered when using the system</li>
                    <li>Feature and interface improvement suggestions</li>
                    <li>New feature requests</li>
                  </ul>
                </Alert>
              </Grid>
            </Grid>
          </form>
        </Paper>
      )}
    </Box>
  );
};

export default FeedbackPage;

