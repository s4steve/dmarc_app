import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { dmarcAPI } from '../utils/api';
import { 
  CloudArrowUpIcon, 
  DocumentIcon,
  CheckCircleIcon,
  XCircleIcon 
} from '@heroicons/react/24/outline';

interface FileUploadProps {
  onUploadSuccess?: () => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [uploadMessage, setUploadMessage] = useState<string>('');
  const [uploadedFiles, setUploadedFiles] = useState<Array<{ name: string; status: string }>>([]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setUploadStatus('uploading');
    setUploadMessage('');
    
    const results = [];
    
    for (const file of acceptedFiles) {
      try {
        const result = await dmarcAPI.uploadReport(file);
        results.push({ name: file.name, status: 'success' });
        setUploadMessage(prev => prev + `✅ ${file.name} uploaded successfully\n`);
      } catch (error: any) {
        results.push({ name: file.name, status: 'error' });
        setUploadMessage(prev => prev + `❌ ${file.name} failed: ${error.response?.data?.detail || 'Unknown error'}\n`);
      }
    }
    
    setUploadedFiles(results);
    
    if (results.every(r => r.status === 'success')) {
      setUploadStatus('success');
      if (onUploadSuccess) {
        onUploadSuccess();
      }
    } else {
      setUploadStatus('error');
    }
  }, [onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/xml': ['.xml'],
      'application/xml': ['.xml']
    },
    multiple: true
  });

  const resetUpload = () => {
    setUploadStatus('idle');
    setUploadMessage('');
    setUploadedFiles([]);
  };

  const getDropzoneStyle = () => {
    if (isDragActive) {
      return { borderColor: '#60A5FA', backgroundColor: '#EFF6FF' };
    } else if (uploadStatus === 'success') {
      return { borderColor: '#34D399', backgroundColor: '#ECFDF5' };
    } else if (uploadStatus === 'error') {
      return { borderColor: '#F87171', backgroundColor: '#FEF2F2' };
    } else {
      return { borderColor: '#D1D5DB', backgroundColor: 'white' };
    }
  };

  return (
    <div style={{ width: '100%', maxWidth: '32rem', margin: '0 auto' }}>
      <div
        {...getRootProps()}
        style={{
          border: '2px dashed',
          borderRadius: '0.5rem',
          padding: '1.5rem',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s',
          ...getDropzoneStyle()
        }}
        onMouseEnter={(e) => {
          if (uploadStatus === 'idle') {
            e.currentTarget.style.borderColor = '#9CA3AF';
          }
        }}
        onMouseLeave={(e) => {
          if (uploadStatus === 'idle') {
            e.currentTarget.style.borderColor = '#D1D5DB';
          }
        }}
      >
        <input {...getInputProps()} />
        
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          {uploadStatus === 'uploading' ? (
            <div style={{ 
              animation: 'spin 1s linear infinite', 
              borderRadius: '50%', 
              height: '3rem', 
              width: '3rem', 
              borderBottom: '2px solid #2563EB', 
              marginBottom: '1rem' 
            }}></div>
          ) : uploadStatus === 'success' ? (
            <CheckCircleIcon style={{ height: '3rem', width: '3rem', color: '#10B981', marginBottom: '1rem' }} />
          ) : uploadStatus === 'error' ? (
            <XCircleIcon style={{ height: '3rem', width: '3rem', color: '#EF4444', marginBottom: '1rem' }} />
          ) : (
            <CloudArrowUpIcon style={{ height: '3rem', width: '3rem', color: '#9CA3AF', marginBottom: '1rem' }} />
          )}
          
          <h3 style={{ fontSize: '1.125rem', fontWeight: '500', color: '#111827', marginBottom: '0.5rem' }}>
            {uploadStatus === 'uploading'
              ? 'Uploading DMARC Reports...'
              : uploadStatus === 'success'
              ? 'Upload Successful!'
              : uploadStatus === 'error'
              ? 'Upload Issues'
              : 'Upload DMARC Reports'
            }
          </h3>
          
          {uploadStatus === 'idle' && (
            <div>
              <p style={{ fontSize: '0.875rem', color: '#6B7280', marginBottom: '0.5rem' }}>
                {isDragActive
                  ? 'Drop the XML files here...'
                  : 'Drag & drop XML files here, or click to select files'
                }
              </p>
              <p style={{ fontSize: '0.75rem', color: '#9CA3AF' }}>
                Accepts XML files from email providers (DMARC aggregate reports)
              </p>
            </div>
          )}
        </div>
      </div>
      
      {uploadMessage && (
        <div style={{ 
          marginTop: '1rem', 
          padding: '1rem', 
          backgroundColor: '#F9FAFB', 
          borderRadius: '0.5rem' 
        }}>
          <h4 style={{ fontSize: '0.875rem', fontWeight: '500', color: '#111827', marginBottom: '0.5rem' }}>Upload Results:</h4>
          <pre style={{ 
            fontSize: '0.75rem', 
            color: '#4B5563', 
            whiteSpace: 'pre-wrap', 
            fontFamily: 'inherit' 
          }}>{uploadMessage}</pre>
        </div>
      )}
      
      {uploadedFiles.length > 0 && (
        <div style={{ marginTop: '1rem' }}>
          <h4 style={{ fontSize: '0.875rem', fontWeight: '500', color: '#111827', marginBottom: '0.5rem' }}>Processed Files:</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {uploadedFiles.map((file, index) => (
              <div key={index} style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between', 
                padding: '0.5rem', 
                backgroundColor: '#F9FAFB', 
                borderRadius: '0.25rem' 
              }}>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <DocumentIcon style={{ height: '1rem', width: '1rem', color: '#9CA3AF', marginRight: '0.5rem' }} />
                  <span style={{ fontSize: '0.875rem', color: '#374151' }}>{file.name}</span>
                </div>
                {file.status === 'success' ? (
                  <CheckCircleIcon style={{ height: '1rem', width: '1rem', color: '#10B981' }} />
                ) : (
                  <XCircleIcon style={{ height: '1rem', width: '1rem', color: '#EF4444' }} />
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {(uploadStatus === 'success' || uploadStatus === 'error') && (
        <div style={{ marginTop: '1rem', textAlign: 'center' }}>
          <button
            onClick={resetUpload}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '0.5rem 1rem',
              border: 'none',
              fontSize: '0.875rem',
              fontWeight: '500',
              borderRadius: '0.375rem',
              color: '#2563EB',
              backgroundColor: 'transparent',
              cursor: 'pointer',
              transition: 'color 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#1D4ED8'}
            onMouseLeave={(e) => e.currentTarget.style.color = '#2563EB'}
          >
            Upload More Files
          </button>
        </div>
      )}
    </div>
  );
};

export default FileUpload;