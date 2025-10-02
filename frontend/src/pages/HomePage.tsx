import React from 'react';
import { Box, Typography, Button, Grid, Card, CardContent, CardActions, Avatar, Paper } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Science as ScienceIcon,
  CloudUpload as UploadIcon,
  Dataset as DatasetIcon,
  Feedback as FeedbackIcon
} from '@mui/icons-material';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const features = [
    {
      icon: <ScienceIcon />,
      title: 'Parameter Query',
      description: 'Input experiment type and get optimal parameter recommendations',
      action: () => navigate('/query'),
      buttonText: 'Start Query',
      color: '#1976d2'
    },
    {
      icon: <UploadIcon />,
      title: 'Data Input',
      description: 'Manually input experimental data to enrich our database',
      action: () => navigate('/input'),
      buttonText: 'Input Data',
      color: '#388e3c'
    },
    {
      icon: <DatasetIcon />,
      title: 'Upload Dataset',
      description: 'Upload your own experimental datasets for analysis and training',
      action: () => navigate('/upload'),
      buttonText: 'Upload Dataset',
      color: '#f57c00'
    },
    {
      icon: <FeedbackIcon />,
      title: 'Submit Feedback',
      description: 'Share your experimental results to improve our models',
      action: () => navigate('/feedback'),
      buttonText: 'Submit Feedback',
      color: '#d32f2f'
    }
  ];

  return (
    <Box>
      {/* Welcome Header */}
      <Paper sx={{ p: 4, mb: 4, background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)', color: 'white' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', mr: 2 }}>
            {user?.name.charAt(0).toUpperCase()}
          </Avatar>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              Welcome back, {user?.name}!
            </Typography>
            <Typography variant="h6" component="h2" color="rgba(255,255,255,0.8)">
              Ready to optimize your experimental design?
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Quick Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h4" color="primary" gutterBottom>
              12
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Experiments Conducted
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h4" color="primary" gutterBottom>
              8
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Successful Predictions
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h4" color="primary" gutterBottom>
              67%
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Success Rate
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Main Features */}
      <Typography variant="h5" component="h2" gutterBottom sx={{ mb: 3 }}>
        What would you like to do?
      </Typography>
      
      <Grid container spacing={4}>
        {features.map((feature, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card 
              sx={{ 
                height: '100%', 
                display: 'flex', 
                flexDirection: 'column',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4
                }
              }}
            >
              <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                <Box 
                  sx={{ 
                    color: feature.color, 
                    fontSize: '3rem', 
                    mb: 2,
                    display: 'flex',
                    justifyContent: 'center'
                  }}
                >
                  {feature.icon}
                </Box>
                <Typography variant="h6" component="h3" gutterBottom>
                  {feature.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {feature.description}
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
                <Button 
                  onClick={feature.action} 
                  variant="contained"
                  sx={{ 
                    bgcolor: feature.color,
                    '&:hover': { bgcolor: feature.color, opacity: 0.9 }
                  }}
                >
                  {feature.buttonText}
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default HomePage;
