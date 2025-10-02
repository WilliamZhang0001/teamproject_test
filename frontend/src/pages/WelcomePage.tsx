import React from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Paper
} from '@mui/material';
import { 
  Science, 
  QueryStats, 
  Upload, 
  Feedback,
  Login,
  PersonAdd
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const WelcomePage: React.FC = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <Science sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Intelligent Parameter Recommendation',
      description: 'Based on literature mining and machine learning, recommend optimal experimental parameter combinations for you'
    },
    {
      icon: <QueryStats sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Experimental Design Optimization',
      description: 'Help you design more efficient experimental plans and reduce the number of experiments'
    },
    {
      icon: <Upload sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Data Upload and Analysis',
      description: 'Support multiple data formats for quick analysis of your experimental data'
    },
    {
      icon: <Feedback sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Result Feedback Learning',
      description: 'Continuously optimize recommendation algorithms through feedback to provide more accurate suggestions'
    }
  ];

  return (
    <Box>
      {/* Hero Section */}
      <Paper
        sx={{
          background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
          color: 'white',
          py: 8,
          mb: 6
        }}
      >
        <Container maxWidth="lg">
          <Box textAlign="center">
            <Typography variant="h2" component="h1" gutterBottom>
              DoE-Assist
            </Typography>
            <Typography variant="h5" component="h2" gutterBottom sx={{ mb: 4 }}>
              Intelligent Experimental Design Assistant
            </Typography>
            <Typography variant="h6" sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}>
              An experimental parameter recommendation system based on literature mining and machine learning,
              helping you optimize experimental design and improve research efficiency
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="contained"
                size="large"
                startIcon={<Login />}
                onClick={() => navigate('/login')}
                sx={{ 
                  bgcolor: 'white', 
                  color: 'primary.main',
                  '&:hover': { bgcolor: 'grey.100' }
                }}
              >
                Sign In
              </Button>
              <Button
                variant="outlined"
                size="large"
                startIcon={<PersonAdd />}
                onClick={() => navigate('/register')}
                sx={{ 
                  borderColor: 'white', 
                  color: 'white',
                  '&:hover': { 
                    borderColor: 'white',
                    bgcolor: 'rgba(255,255,255,0.1)'
                  }
                }}
              >
                Sign Up
              </Button>
            </Box>
          </Box>
        </Container>
      </Paper>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ mb: 8 }}>
        <Typography variant="h3" component="h2" textAlign="center" gutterBottom sx={{ mb: 6 }}>
          Core Features
        </Typography>
        
        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} md={6} key={index}>
              <Card sx={{ height: '100%', textAlign: 'center' }}>
                <CardContent sx={{ p: 4 }}>
                  <Box sx={{ mb: 2 }}>
                    {feature.icon}
                  </Box>
                  <Typography variant="h5" component="h3" gutterBottom>
                    {feature.title}
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    {feature.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* CTA Section */}
      <Paper sx={{ py: 6, bgcolor: 'grey.50' }}>
        <Container maxWidth="md" sx={{ textAlign: 'center' }}>
          <Typography variant="h4" component="h2" gutterBottom>
            Start Your Intelligent Experimental Design Journey
          </Typography>
          <Typography variant="h6" color="text.secondary" paragraph sx={{ mb: 4 }}>
            Register now to experience AI-driven experimental parameter recommendations
          </Typography>
          <Button
            variant="contained"
            size="large"
            startIcon={<PersonAdd />}
            onClick={() => navigate('/register')}
          >
            Free Registration
          </Button>
        </Container>
      </Paper>
    </Box>
  );
};

export default WelcomePage;
