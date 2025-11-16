import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Box, Typography, Button, Paper, Container } from '@mui/material';
import { Error as ErrorIcon, Refresh as RefreshIcon } from '@mui/icons-material';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <Container maxWidth="md" sx={{ mt: 8, mb: 4 }}>
          <Paper sx={{ p: 4 }}>
            <Box sx={{ textAlign: 'center' }}>
              <ErrorIcon sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
              <Typography variant="h4" gutterBottom>
                Something went wrong
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                We're sorry, the application encountered a problem. Please try refreshing the page or returning to the home page.
              </Typography>
              
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <Box sx={{ mt: 3, p: 2, bgcolor: 'error.light', borderRadius: 1, textAlign: 'left' }}>
                  <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                    {this.state.error.toString()}
                  </Typography>
                </Box>
              )}
              
              <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'center' }}>
                <Button
                  variant="contained"
                  startIcon={<RefreshIcon />}
                  onClick={this.handleReset}
                >
                  Retry
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => window.location.href = '/'}
                >
                  Return to Home
                </Button>
              </Box>
            </Box>
          </Paper>
        </Container>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

