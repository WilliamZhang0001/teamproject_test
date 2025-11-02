import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, Grid, Card, CardContent, CardActions, Avatar, Paper, LinearProgress, Chip, Alert, CircularProgress } from '@mui/material';
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
import { experimentService, ExperimentHistory } from '../services/experimentService';
import { formatDate } from '../utils/formatters';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [history, setHistory] = useState<ExperimentHistory[]>([]);

  // Calculate statistics from real data
  const calculateStats = (hist: ExperimentHistory[]) => {
    const total = hist.length;
    
    // Parse prediction results
    const goodPredictions = hist.filter(h => {
      try {
        const result = typeof h.prediction_result === 'string' 
          ? JSON.parse(h.prediction_result) 
          : h.prediction_result;
        return result?.prediction === 'Good' || result?.data?.prediction === 'Good';
      } catch {
        return false;
      }
    }).length;
    
    const badPredictions = hist.filter(h => {
      try {
        const result = typeof h.prediction_result === 'string' 
          ? JSON.parse(h.prediction_result) 
          : h.prediction_result;
        return result?.prediction === 'Bad' || result?.data?.prediction === 'Bad';
      } catch {
        return false;
      }
    }).length;
    
    const avgConfidence = total > 0
      ? hist.reduce((sum, h) => sum + (h.confidence || 0), 0) / total * 100
      : 0;
    
    // Get experiments from this week
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
    const recentActivity = hist.filter(h => {
      const createdDate = new Date(h.created_at);
      return createdDate >= oneWeekAgo;
    }).length;
    
    return {
      totalExperiments: total,
      successfulPredictions: goodPredictions,
      successRate: total > 0 ? Math.round((goodPredictions / total) * 100) : 0,
      avgConfidence: Math.round(avgConfidence),
      recentActivity
    };
  };

  const stats = calculateStats(history);

  // Generate trend data from history (last 6 months)
  const generateTrendData = (hist: ExperimentHistory[]) => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const sixMonthsAgo = new Date();
    sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
    
    const filtered = hist.filter(h => new Date(h.created_at) >= sixMonthsAgo);
    
    // Group by month
    const byMonth: { [key: string]: { experiments: number; success: number } } = {};
    
    filtered.forEach(h => {
      const date = new Date(h.created_at);
      const monthKey = `${date.getFullYear()}-${date.getMonth()}`;
      
      if (!byMonth[monthKey]) {
        byMonth[monthKey] = { experiments: 0, success: 0 };
      }
      
      byMonth[monthKey].experiments++;
      
      try {
        const result = typeof h.prediction_result === 'string' 
          ? JSON.parse(h.prediction_result) 
          : h.prediction_result;
        if (result?.prediction === 'Good' || result?.data?.prediction === 'Good') {
          byMonth[monthKey].success++;
        }
      } catch {
        // Skip if parsing fails
      }
    });
    
    // Convert to array and get last 6 months
    const trendData: { month: string; experiments: number; success: number }[] = [];
    for (let i = 5; i >= 0; i--) {
      const date = new Date();
      date.setMonth(date.getMonth() - i);
      const monthKey = `${date.getFullYear()}-${date.getMonth()}`;
      const monthName = months[date.getMonth()];
      
      trendData.push({
        month: monthName,
        experiments: byMonth[monthKey]?.experiments || 0,
        success: byMonth[monthKey]?.success || 0
      });
    }
    
    return trendData;
  };

  const experimentTrendData = generateTrendData(history);

  // Generate experiment type distribution
  const generateExperimentTypeData = (hist: ExperimentHistory[]) => {
    const typeCounts: { [key: string]: number } = {};
    
    hist.forEach(h => {
      const type = h.experiment_type || 'stability';
      typeCounts[type] = (typeCounts[type] || 0) + 1;
    });
    
    const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088fe', '#00c49f'];
    let colorIndex = 0;
    
    return Object.entries(typeCounts)
      .map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value,
        color: colors[colorIndex++ % colors.length]
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 6); // Top 6 types
  };

  const experimentTypeData = generateExperimentTypeData(history);

  // Get recent experiments (last 3)
  const recentExperiments = history
    .slice(0, 3)
    .map(h => {
      let prediction = '';
      try {
        const result = typeof h.prediction_result === 'string' 
          ? JSON.parse(h.prediction_result) 
          : h.prediction_result;
        prediction = result?.prediction || result?.data?.prediction || 'N/A';
      } catch {
        prediction = 'N/A';
      }
      
      return {
        id: h.id,
        name: `${h.biomolecule_name} - ${h.experiment_type}`,
        type: h.experiment_type,
        status: prediction === 'Good' ? 'completed' : prediction === 'Bad' ? 'warning' : 'pending',
        date: formatDate(h.created_at),
        biomoleculeName: h.biomolecule_name,
        confidence: h.confidence
      };
    });

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await experimentService.getHistory(100);
      setHistory(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

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
      action: () => navigate('/results'),
      buttonText: 'View Experiments',
      color: '#9c27b0'
    },
    {
      icon: <UploadIcon />,
      title: 'Literature Search',
      description: 'Search for similar literature based on experimental conditions to get reference data',
      action: () => navigate('/input'),
      buttonText: 'Search Literature',
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

      {/* Main Features */}
      <Grid container spacing={4} sx={{ mb: 4 }}>
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

      {/* Loading State */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Enhanced Stats */}
      {!loading && (
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
                Good Predictions
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
              <AssessmentIcon sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
              <Typography variant="h4" color="warning.main" gutterBottom>
                {stats.avgConfidence}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Avg Confidence
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
      )}

      {/* Charts Section - Only show if there's data */}
      {!loading && history.length > 0 && (
        <>
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={8}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  <TrendingUpIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Experiment Trends (Last 6 Months)
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
            
            {experimentTypeData.length > 0 && (
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
                          label={({ name, value }) => `${name}: ${value}`}
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
            )}
          </Grid>
        </>
      )}

      {/* Recent Activity */}
      {!loading && (
        <Paper sx={{ p: 3, mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            <TimelineIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Recent Experiments
          </Typography>
          {recentExperiments.length > 0 ? (
            <>
              <Grid container spacing={2}>
                {recentExperiments.map((experiment) => (
                  <Grid item xs={12} sm={6} md={4} key={experiment.id}>
                    <Card variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                          <Typography variant="subtitle1" noWrap>
                            {experiment.biomoleculeName}
                          </Typography>
                          <Chip 
                            label={experiment.type} 
                            size="small"
                            color="primary"
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {experiment.type} • {experiment.date}
                        </Typography>
                        {experiment.confidence !== null && experiment.confidence !== undefined && (
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            Confidence: {(experiment.confidence * 100).toFixed(1)}%
                          </Typography>
                        )}
                        <Button 
                          size="small" 
                          onClick={() => navigate('/results')}
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
                  onClick={() => navigate('/results')}
                >
                  View All Experiments
                </Button>
              </Box>
            </>
          ) : (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body1" color="text.secondary" gutterBottom>
                No experiments yet. Start your first prediction!
              </Typography>
              <Button 
                variant="contained" 
                onClick={() => navigate('/query')}
                sx={{ mt: 2 }}
              >
                Start Parameter Query
              </Button>
            </Box>
          )}
        </Paper>
      )}
    </Box>
  );
};

export default HomePage;
