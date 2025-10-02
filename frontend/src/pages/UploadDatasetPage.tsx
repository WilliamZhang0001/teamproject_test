import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Alert,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton
} from '@mui/material';
import { CloudUpload, Delete, CheckCircle } from '@mui/icons-material';

const UploadDatasetPage: React.FC = () => {
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setMessage(null);

    try {
      // TODO: Implement actual file upload logic
      // For now, simulate upload
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const newFiles = Array.from(files).map(file => file.name);
      setUploadedFiles(prev => [...prev, ...newFiles]);
      setMessage({ type: 'success', text: 'File uploaded successfully!' });
    } catch (error) {
      setMessage({ type: 'error', text: 'File upload failed, please try again.' });
    } finally {
      setUploading(false);
    }
  };

  const handleRemoveFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <Container maxWidth="md">
      <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dataset Upload
        </Typography>
        
        <Typography variant="body1" color="text.secondary" paragraph>
          Upload your experimental dataset files, supporting CSV, Excel and other formats.
        </Typography>

        {message && (
          <Alert severity={message.type} sx={{ mb: 3 }}>
            {message.text}
          </Alert>
        )}

        <Box sx={{ mb: 4 }}>
          <input
            accept=".csv,.xlsx,.xls"
            style={{ display: 'none' }}
            id="file-upload"
            multiple
            type="file"
            onChange={handleFileUpload}
            disabled={uploading}
          />
          <label htmlFor="file-upload">
            <Button
              variant="contained"
              component="span"
              startIcon={<CloudUpload />}
              disabled={uploading}
              sx={{ mb: 2 }}
            >
              Select Files
            </Button>
          </label>
          
          {uploading && (
            <Box sx={{ width: '100%', mt: 2 }}>
              <LinearProgress />
              <Typography variant="body2" sx={{ mt: 1 }}>
                Uploading files...
              </Typography>
            </Box>
          )}
        </Box>

        {uploadedFiles.length > 0 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Uploaded Files
            </Typography>
            <List>
              {uploadedFiles.map((fileName, index) => (
                <ListItem key={index} divider>
                  <CheckCircle color="success" sx={{ mr: 2 }} />
                  <ListItemText primary={fileName} />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      onClick={() => handleRemoveFile(index)}
                      color="error"
                    >
                      <Delete />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        <Box sx={{ mt: 4, display: 'flex', gap: 2 }}>
          <Button variant="contained" disabled={uploadedFiles.length === 0}>
            Process Dataset
          </Button>
          <Button variant="outlined">
            View Example Format
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default UploadDatasetPage;
