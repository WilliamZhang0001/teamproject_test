import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, Grid, Card, CardContent, CardActions, Avatar, Paper, LinearProgress, Chip, Alert } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Science as ScienceIcon,
  CloudUpload as UploadIcon,
  Dataset as DatasetIcon,
  Feedback as FeedbackIcon,
  TrendingUp as TrendingUpIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Mock data for charts and statistics
  const [stats, setStats] = useState({
    totalExperiments: 12,
    successfulPredictions: 8,
    successRate: 67,
    totalFeedback: 5,
    recentActivity: 3
  });

  const experimentTrendData = [
    { month: 'Jan', experiments: 2, success: 1 },
    { month: 'Feb', experiments: 3, success: 2 },
    { month: 'Mar', experiments: 4, success: 3 },
    { month: 'Apr', experiments: 3, success: 2 },
    { month: 'May', experiments: 5, success: 4 },
    { month: 'Jun', experiments: 4, success: 3 }
  ];

  const experimentTypeData = [
    { name: 'Solubility', value: 45, color: '#8884d8' },
    { name: 'Crystallization', value: 25, color: '#82ca9d' },
    { name: 'Reaction', value: 20, color: '#ffc658' },
    { name: 'Extraction', value: 10, color: '#ff7300' }
  ];

  const recentExperiments = [
    { id: 1, name: 'Solubility Study - Compound A', type: 'solubility', status: 'completed', date: '2024-01-15' },
    { id: 2, name: 'Crystallization Optimization', type: 'crystallization', status: 'running', date: '2024-01-16' },
    { id: 3, name: 'Reaction Kinetics Analysis', type: 'reaction', status: 'draft', date: '2024-01-17' }
  ];

  useEffect(() => {
    // Simulate fetching user statistics
    // In a real app, this would fetch from the backend
  }, []);

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
      icon: <DatasetIcon />,
      title: 'My Experiments',
      description: 'View and manage your experimental projects',
      action: () => navigate('/experiments'),
      buttonText: 'View Experiments',
      color: '#9c27b0'
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

      {/* Enhanced Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={2.4}>
          <Paper sx={{ p: 3, textAlign: 'center', height: '100%' }}>
            <AssessmentIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
            <Typography variant="h4" color="primary" gutterBottom>
              {stats.totalExperiments}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Total Experiments
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Paper sx={{ p: 3, textAlign: 'center', height: '100%' }}>
            <CheckCircleIcon sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
            <Typography variant="h4" color="success.main" gutterBottom>
              {stats.successfulPredictions}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Successful Predictions
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Paper sx={{ p: 3, textAlign: 'center', height: '100%' }}>
            <TrendingUpIcon sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
            <Typography variant="h4" color="info.main" gutterBottom>
              {stats.successRate}%
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Success Rate
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={stats.successRate} 
              sx={{ mt: 1, height: 4, borderRadius: 2 }}
            />
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Paper sx={{ p: 3, textAlign: 'center', height: '100%' }}>
            <FeedbackIcon sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
            <Typography variant="h4" color="warning.main" gutterBottom>
              {stats.totalFeedback}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Feedback Submitted
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Paper sx={{ p: 3, textAlign: 'center', height: '100%' }}>
            <TimelineIcon sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
            <Typography variant="h4" color="secondary.main" gutterBottom>
              {stats.recentActivity}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              This Week
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Charts Section */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              <TrendingUpIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Experiment Trends
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={experimentTrendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Area 
                    type="monotone" 
                    dataKey="experiments" 
                    stackId="1" 
                    stroke="#8884d8" 
                    fill="#8884d8" 
                    fillOpacity={0.6}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="success" 
                    stackId="1" 
                    stroke="#82ca9d" 
                    fill="#82ca9d" 
                    fillOpacity={0.6}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              <AssessmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Experiment Types
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={experimentTypeData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}%`}
                  >
                    {experimentTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          <TimelineIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Recent Experiments
        </Typography>
        <Grid container spacing={2}>
          {recentExperiments.map((experiment) => (
            <Grid item xs={12} sm={6} md={4} key={experiment.id}>
              <Card variant="outlined">
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Typography variant="subtitle1" noWrap>
                      {experiment.name}
                    </Typography>
                    <Chip 
                      label={experiment.status} 
                      size="small"
                      color={
                        experiment.status === 'completed' ? 'success' :
                        experiment.status === 'running' ? 'info' : 'warning'
                      }
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {experiment.type} • {experiment.date}
                  </Typography>
                  <Button 
                    size="small" 
                    onClick={() => navigate(`/experiments/${experiment.id}`)}
                    sx={{ mt: 1 }}
                  >
                    View Details
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
        <Box sx={{ textAlign: 'center', mt: 2 }}>
          <Button 
            variant="outlined" 
            onClick={() => navigate('/experiments')}
          >
            View All Experiments
          </Button>
        </Box>
      </Paper>

      {/* Main Features */}
      <Typography variant="h5" component="h2" gutterBottom sx={{ mb: 3 }}>
        What would you like to do?
      </Typography>
      
      <Grid container spacing={4}>
        {features.map((feature, index) => (
          <Grid item xs={12} sm={6} md={2.4} key={index}>
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
