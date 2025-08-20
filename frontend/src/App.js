import React, { useState, useEffect } from "react";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Paper from "@mui/material/Paper";
import RefreshIcon from "@mui/icons-material/Refresh";
import Typography from "@mui/material/Typography";
import Modal from "@mui/material/Modal";
import IconButton from "@mui/material/IconButton";
import CloseIcon from "@mui/icons-material/Close";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import Tooltip from '@mui/material/Tooltip';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DeleteForeverIcon from '@mui/icons-material/DeleteForever';


// Evidence Modal Component
const EvidenceModal = ({ open, onClose, evidenceData, loading, error }) => {
  const [verifyMode, setVerifyMode] = useState(null);
  const [correctionValue, setCorrectionValue] = useState("");
  const [correctionFeedback, setCorrectionFeedback] = useState("");
  const [submitted, setSubmitted] = useState(false);

  return (
    <Modal
      open={open}
      onClose={onClose}
      aria-labelledby="evidence-modal-title"
      aria-describedby="evidence-modal-description"
    >
      <Box sx={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: { xs: '95%', md: '80%' },
        maxWidth: 800,
        maxHeight: '90vh',
        bgcolor: 'background.paper',
        borderRadius: 3,
        boxShadow: 24,
        p: 3,
        overflow: 'auto',
        direction: 'rtl'
      }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography id="evidence-modal-title" variant="h5" component="h2" sx={{ fontWeight: 'bold', color: '#1e6641' }}>
            دليل الاستخراج - الأرباح المبقاة
          </Typography>
          <IconButton onClick={onClose} sx={{ color: '#666' }}>
            <CloseIcon />
          </IconButton>
        </Box>

        {/* Content */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
            <CircularProgress sx={{ color: '#1e6641' }} />
            <Typography sx={{ ml: 2, color: '#666' }}>جاري تحميل الدليل...</Typography>
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {evidenceData && !loading && (
          <Box>
            {/* Screenshot */}
            {evidenceData.screenshot_url && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, color: '#1e6641' }}>
                  لقطة شاشة من المستند
                </Typography>
                <Box sx={{ 
                  display: 'flex', 
                  justifyContent: 'center',
                  border: '2px solid #e0e0e0',
                  borderRadius: 2,
                  overflow: 'hidden',
                  bgcolor: '#fafafa'
                }}>
                  <img 
                    src={`http://localhost:5003${evidenceData.screenshot_url}`} 
                    alt="Evidence Screenshot"
                    style={{ 
                      maxWidth: '100%', 
                      maxHeight: '400px',
                      objectFit: 'contain'
                    }}
                  />
                </Box>
              </Box>
            )}

            {/* Raw Text Context */}
            {evidenceData.context && (
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 2, color: '#1e6641' }}>
                  النص المستخرج
                </Typography>
                <Box sx={{ 
                  p: 2, 
                  bgcolor: '#f8f9fa', 
                  borderRadius: 2,
                  border: '1px solid #e0e0e0',
                  fontFamily: 'monospace',
                  fontSize: '14px',
                  whiteSpace: 'pre-wrap',
                  maxHeight: '200px',
                  overflow: 'auto'
                }}>
                  {evidenceData.context}
                </Box>
              </Box>
            )}
            {evidenceData && evidenceData.context && !loading && (
              <Box sx={{ mt: 2, textAlign: 'left' }}>
                <Tooltip title="تعديل النتيجة" arrow>
                  <IconButton
                    size="small"
                    sx={{ color: '#1e6641', opacity: 0.7, ml: 1, '&:hover': { opacity: 1, bgcolor: '#e8f5ee' } }}
                    onClick={() => setVerifyMode(verifyMode ? null : 'form')}
                  >
                    <InfoOutlinedIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                {verifyMode === 'form' && (
                  <Box sx={{ mt: 1, display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <TextField
                      size="small"
                      label="القيمة الصحيحة"
                      value={correctionValue}
                      onChange={e => setCorrectionValue(e.target.value)}
                      sx={{ maxWidth: 180 }}
                    />
                    <TextField
                      size="small"
                      label="ملاحظات (اختياري)"
                      value={correctionFeedback}
                      onChange={e => setCorrectionFeedback(e.target.value)}
                      sx={{ maxWidth: 250 }}
                    />
                    <Button
                      size="small"
                      variant="contained"
                      color="primary"
                      sx={{ fontSize: 13, px: 2, py: 0.5, mt: 1, alignSelf: 'flex-start' }}
                      onClick={async () => {
                        setSubmitted(true);
                        // Send correction to backend
                        try {
                          const res = await fetch('http://localhost:5003/api/correct_retained_earnings', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                              company_symbol: evidenceData.company_symbol || evidenceData.symbol,
                              correct_value: correctionValue,
                              feedback: correctionFeedback,
                            })
                          });
                          const data = await res.json();
                          if (data.status === 'success' && data.updated) {
                            if (typeof window.updateRowAfterCorrection === 'function') {
                              window.updateRowAfterCorrection(data.updated);
                            }
                          }
                        } catch (e) {}
                        setVerifyMode(null);
                      }}
                    >
                      إرسال التصحيح
                    </Button>
                    {submitted && (
                      <Typography sx={{ color: '#1e6641', fontSize: 14, mt: 1 }}>شكرًا لملاحظتك! تم تسجيل التصحيح.</Typography>
                    )}
                  </Box>
                )}
                {submitted && !verifyMode && (
                  <Typography sx={{ color: '#1e6641', fontSize: 14, mt: 1 }}>شكرًا لملاحظتك! تم تسجيل التصحيح.</Typography>
                )}
              </Box>
            )}
          </Box>
        )}
      </Box>
    </Modal>
  );
};

const FIELD_NAMES = [
  'DATE',
  'Saudi_ValueTraded_Individuals',
  'Saudi_ValueTraded_Institutions',
  'GCC_ValueTraded_Total',
  'Foreign_ValueTraded_Total',
  'Saudi_Holding_Value_Individuals',
  'Saudi_Holding_Value_Institutions',
  'GCC_Holding_Value_Total',
  'Foreign_Holding_Value_Total',
  'Saudi_Weekly_Change_Individuals',
  'Saudi_Weekly_Change_Institutions',
  'GCC_Weekly_Change_Total',
  'Foreign_Weekly_Change_Total',
  'Ownership Value',
  'Saudi_OwnershipValue_Individuals',
  'Saudi_OwnershipValue_Institutions',
  'GCC_OwnershipValue_Total',
  'Foreign_OwnershipValue_Total',
];

function App() {
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [evidenceModalOpen, setEvidenceModalOpen] = useState(false);
  const [evidenceData, setEvidenceData] = useState(null);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [evidenceError, setEvidenceError] = useState(null);
  const [snapshots, setSnapshots] = useState([]);
  const [snapshotsLoading, setSnapshotsLoading] = useState(false);
  const [snapshotsError, setSnapshotsError] = useState(null);
  const [userExports, setUserExports] = useState([]);
  const [userExportsLoading, setUserExportsLoading] = useState(false);
  const [userExportsError, setUserExportsError] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [fileToDelete, setFileToDelete] = useState(null);
  // Upload state
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [showUploadConfirmation, setShowUploadConfirmation] = useState(false);
  const [showClearConfirmation, setShowClearConfirmation] = useState(false);
  // Store extracted data as columns
  const [pdfColumns, setPdfColumns] = useState(() => {
    // Load from localStorage if available
    const saved = localStorage.getItem('pdfColumns');
    return saved ? JSON.parse(saved) : [];
  });

  // Update localStorage whenever pdfColumns changes
  useEffect(() => {
    localStorage.setItem('pdfColumns', JSON.stringify(pdfColumns));
  }, [pdfColumns]);

  // Clean up failed uploads on component mount
  useEffect(() => {
    cleanFailedUploads();
  }, []);

  // Function to fetch evidence data
  const fetchEvidence = async (companySymbol) => {
    setEvidenceLoading(true);
    setEvidenceError(null);
    
    try {
      const response = await fetch(`http://localhost:5003/api/evidence/${companySymbol}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setEvidenceData(data);
    } catch (error) {
      console.error('Error fetching evidence:', error);
      setEvidenceError('فشل في تحميل دليل الاستخراج. تأكد من تشغيل خادم الأدلة.');
    } finally {
      setEvidenceLoading(false);
    }
  };

  // Function to handle evidence button click
  const handleEvidenceClick = (row) => {
    if (row.retained_earnings && row.retained_earnings !== "لايوجد") {
      setEvidenceModalOpen(true);
      fetchEvidence(row.symbol);
    }
  };

  // Function to handle reset (إعادة تعيين)
  const handleReset = async () => {
    setLoading(true);
    try {
      // Clean up failed uploads first
      cleanFailedUploads();
      
      const response = await fetch('http://localhost:5003/api/refresh', {
        method: 'POST',
      });
      const data = await response.json();
      if (data.status === 'success') {
        alert('تم إعادة تعيين البيانات بنجاح');
      } else {
        alert('حدث خطأ أثناء التحديث: ' + (data.message || ''));
        setLoading(false);
      }
    } catch (error) {
      alert('تعذر الاتصال بالخادم: ' + error.message);
      setLoading(false);
    }
  };

  // Function to handle Excel export
  const handleExcelExport = async () => {
    try {
      // Filter out failed uploads to match what's displayed in the table
      const successfulColumns = pdfColumns.filter(col => col.data && !col.error);
      
      if (successfulColumns.length === 0) {
        alert('لا توجد بيانات للتصدير. قم برفع ملفات PDF أولاً.');
        return;
      }
      
      // Prepare the data for export
      const exportData = successfulColumns.map(col => ({
        DATE: col.data.DATE || '',
        Saudi_ValueTraded_Individuals: col.data.Saudi_ValueTraded_Individuals || '',
        Saudi_ValueTraded_Institutions: col.data.Saudi_ValueTraded_Institutions || '',
        GCC_ValueTraded_Total: col.data.GCC_ValueTraded_Total || '',
        Foreign_ValueTraded_Total: col.data.Foreign_ValueTraded_Total || '',
        Saudi_OwnershipValue_Individuals: col.data.Saudi_OwnershipValue_Individuals || '',
        Saudi_OwnershipValue_Institutions: col.data.Saudi_OwnershipValue_Institutions || '',
        GCC_OwnershipValue_Total: col.data.GCC_OwnershipValue_Total || '',
        Foreign_OwnershipValue_Total: col.data.Foreign_OwnershipValue_Total || '',
      }));
      
      // Send the current table data to backend for export
      const response = await fetch('http://localhost:5003/api/export_current_table', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ data: exportData }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // Get the filename from the response headers
      const contentDisposition = response.headers.get('content-disposition');
      let filename = 'dashboard_table.xlsx';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      // Refetch user exports so the new file appears in the sidebar
      setUserExportsLoading(true);
      fetch('http://localhost:5003/api/user_exports')
        .then(res => res.json())
        .then(data => {
          setUserExports(data);
          setUserExportsLoading(false);
        })
        .catch(err => {
          setUserExportsError('فشل في تحميل ملفات قام المستخدم بحفظها');
          setUserExportsLoading(false);
        });
    } catch (error) {
      console.error('Error exporting to Excel:', error);
      alert('فشل في تصدير ملف Excel: ' + error.message);
    }
  };

    // File selection handler
  const handleFileSelection = (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;
    
    // Check for duplicate files
    const duplicates = files.filter(file => 
      pdfColumns.some(col => col.filename === file.name)
    );
    
    if (duplicates.length > 0) {
      const duplicateNames = duplicates.map(f => f.name).join(', ');
      alert(`الملفات التالية موجودة مسبقاً: ${duplicateNames}`);
      return;
    }
    
    // Check for non-PDF files
    const nonPdfFiles = files.filter(file => file.type !== 'application/pdf');
    if (nonPdfFiles.length > 0) {
      const nonPdfNames = nonPdfFiles.map(f => f.name).join(', ');
      alert(`الملفات التالية ليست ملفات PDF: ${nonPdfNames}`);
      return;
    }
    
    setSelectedFiles(files);
    setShowUploadConfirmation(true);
  };

  // Modified upload handler
  const handleFileUpload = async () => {
    setUploading(true);
    setShowUploadConfirmation(false);
    const newColumns = [];
    
    try {
      // Use the new multiple file upload endpoint for better performance
      const formData = new FormData();
      
      // Add all files to the form data
      selectedFiles.forEach((file, index) => {
        formData.append('files[]', file);
      });
      
      const response = await fetch('http://localhost:5003/api/upload_multiple_pdfs', {
        method: 'POST',
        body: formData,
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Process batch results
        console.log(`Batch upload completed: ${result.successful_uploads}/${result.total_files} successful`);
        
        // Add successful uploads to the table
        result.results.forEach((fileResult, index) => {
          if (fileResult.success && fileResult.data) {
            newColumns.push({
              filename: fileResult.filename,
              data: fileResult.data,
              screenshot_path: fileResult.screenshot_paths && fileResult.screenshot_paths.length > 0 ? fileResult.screenshot_paths[0] : null,
            });
          } else {
            // Show error for failed files
            alert(`فشل في استخراج البيانات من "${fileResult.filename}": ${fileResult.error || 'فشل في الاستخراج'}`);
          }
        });
        
        // Show batch summary
        if (result.successful_uploads > 0) {
          alert(`تم رفع ${result.successful_uploads} من ${result.total_files} ملف بنجاح!`);
        }
      } else {
        alert(`فشل في رفع الملفات: ${result.error || 'خطأ غير معروف'}`);
      }
      
    } catch (error) {
      console.error('Error during batch upload:', error);
      alert(`فشل في رفع الملفات: ${error.message}`);
    }
    
    // Only append successful uploads to the table
    if (newColumns.length > 0) {
      setPdfColumns(prev => [...prev, ...newColumns]);
    }
    
    setUploading(false);
    setSelectedFiles([]);
  };

  // Cancel upload confirmation
  const cancelUpload = () => {
    setShowUploadConfirmation(false);
    setSelectedFiles([]);
  };

  // Delete handler
  const handleDeleteExport = (file) => {
    setFileToDelete(file);
    setDeleteDialogOpen(true);
  };

  const confirmDeleteExport = async () => {
    if (!fileToDelete) return;
    try {
              await fetch(`http://localhost:5003/api/user_exports/${fileToDelete.filename}`, { method: 'DELETE' });
      setUserExports((prev) => prev.filter(f => f.filename !== fileToDelete.filename));
    } catch (e) {}
    setDeleteDialogOpen(false);
    setFileToDelete(null);
  };

  const cancelDeleteExport = () => {
    setDeleteDialogOpen(false);
    setFileToDelete(null);
  };

  // Helper: build DataGrid columns from FIELD_NAMES
  const getPdfDataGridColumns = () => [
    {
      field: "filename",
      headerName: "اسم الملف",
      width: 220,
      align: "right",
      headerAlign: "right",
      sortable: true,
    },
    ...FIELD_NAMES.map((field) => ({
      field,
      headerName: field,
      width: 180,
      align: "center",
      headerAlign: "center",
      sortable: true,
      renderCell: (params) => {
        const value = params.value;
        if (!value || value === "" || value === "null" || value === "undefined") {
          return <span style={{ color: '#b71c1c' }}>لايوجد</span>;
        }
        const numValue = parseFloat(value);
        if (!isNaN(numValue)) {
          const formatted = numValue.toLocaleString('en-US');
          const color = numValue < 0 ? '#d32f2f' : numValue > 0 ? '#2e7d32' : '#666';
          return <span style={{ color, fontWeight: 500 }}>{formatted}</span>;
        }
        return value;
      },
    })),
    {
      field: "evidence",
      headerName: "دليل الاستخراج",
      width: 140,
      align: "center",
      headerAlign: "center",
      sortable: false,
      renderCell: (params) => {
        const row = params.row;
        return row.screenshot_path ? (
                                                             <img src={`http://localhost:5003${row.screenshot_path}`} alt="Evidence" style={{ maxWidth: 80, maxHeight: 80, border: '1px solid #ccc', borderRadius: 4 }} />
        ) : (
          <span style={{ color: '#b71c1c' }}>لايوجد</span>
        );
      },
    },
  ];

  // Helper: build DataGrid rows from pdfColumns
  const getPdfDataGridRows = (pdfColumns) =>
    pdfColumns.map((col, idx) => ({
      id: idx,
      filename: col.filename,
      screenshot_path: col.screenshot_path,
      ...col.data,
    }));

  // Custom hierarchical header component
  const HierarchicalHeader = () => (
    <Box sx={{ 
      display: 'grid', 
      gridTemplateColumns: 'minmax(150px, 200px) repeat(8, minmax(120px, 1fr))', // More responsive column widths
      gridTemplateRows: 'auto auto auto', // Three rows for header
      border: '1px solid #e0e0e0',
      borderRadius: '8px 8px 0 0',
      overflow: 'hidden',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      width: '100%'
    }}>
      {/* DATE column - spans 3 rows */}
      <Box sx={{
        gridRow: '1 / 4',
        gridColumn: '1',
        bgcolor: '#fff',
        border: '1px solid #e0e0e0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 'bold',
        fontSize: 16,
        p: 2,
        borderRight: '2px solid #e0e0e0'
      }}>
        DATE
      </Box>

      {/* Value Traded - spans 4 columns */}
      <Box sx={{
        gridRow: '1',
        gridColumn: '2 / 6',
        bgcolor: '#1e6641',
        color: 'white',
        border: '1px solid #e0e0e0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 'bold',
        fontSize: 16,
        p: 2,
        textAlign: 'center'
      }}>
        Value Traded
      </Box>

      {/* Ownership Value - spans 4 columns */}
      <Box sx={{
        gridRow: '1',
        gridColumn: '6 / 10',
        bgcolor: '#1e6641',
        color: 'white',
        border: '1px solid #e0e0e0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 'bold',
        fontSize: 16,
        p: 2,
        textAlign: 'center'
      }}>
        Ownership Value
      </Box>

      {/* Second row - subcategories */}
      {/* Value Traded subcategories */}
      <Box sx={{ 
        gridRow: '2', 
        gridColumn: '2 / 4', 
        bgcolor: '#f8f9fa', 
        border: '1px solid #e0e0e0', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        fontWeight: 'bold', 
        fontSize: 14, 
        p: 1.5,
        color: '#495057'
      }}>
        Saudi
      </Box>
      <Box sx={{ 
        gridRow: '2', 
        gridColumn: '4', 
        bgcolor: '#f8f9fa', 
        border: '1px solid #e0e0e0', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        fontWeight: 'bold', 
        fontSize: 14, 
        p: 1.5,
        color: '#495057'
      }}>
        GCC
      </Box>
      <Box sx={{ 
        gridRow: '2', 
        gridColumn: '5', 
        bgcolor: '#f8f9fa', 
        border: '1px solid #e0e0e0', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        fontWeight: 'bold', 
        fontSize: 14, 
        p: 1.5,
        color: '#495057'
      }}>
        Foreign
      </Box>

      {/* Ownership Value subcategories */}
      <Box sx={{ 
        gridRow: '2', 
        gridColumn: '6 / 8', 
        bgcolor: '#f8f9fa', 
        border: '1px solid #e0e0e0', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        fontWeight: 'bold', 
        fontSize: 14, 
        p: 1.5,
        color: '#495057'
      }}>
        Saudi
      </Box>
      <Box sx={{ 
        gridRow: '2', 
        gridColumn: '8', 
        bgcolor: '#f8f9fa', 
        border: '1px solid #e0e0e0', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        fontWeight: 'bold', 
        fontSize: 14, 
        p: 1.5,
        color: '#495057'
      }}>
        GCC
      </Box>
      <Box sx={{ 
        gridRow: '2', 
        gridColumn: '9', 
        bgcolor: '#f8f9fa', 
        border: '1px solid #e0e0e0', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        fontWeight: 'bold', 
        fontSize: 14, 
        p: 1.5,
        color: '#495057'
      }}>
        Foreign
      </Box>

      {/* Third row - individual columns (these are the actual data fields) */}
      {/* Value Traded - Saudi Individuals */}
      <Box sx={{ 
        gridRow: '3', 
        gridColumn: '2', 
        bgcolor: '#fff', 
        border: '1px solid #e0e0e0', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        fontWeight: 'bold', 
        fontSize: 12, 
        p: 1,
        color: '#6c757d'
      }}>
        Individuals
      </Box>
      {/* Value Traded - Saudi Institutions */}
      <Box sx={{ 
        gridRow: '3', 
        gridColumn: '3', 
        bgcolor: '#fff', 
        border: '1px solid #e0e0e0', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        fontWeight: 'bold', 
        fontSize: 12, 
        p: 1,
        color: '#6c757d'
      }}>
        Institutions
      </Box>
      {/* Value Traded - GCC */}
      <Box sx={{ 
        gridRow: '3', 
        gridColumn: '4', 
        bgcolor: '#fff', 
        border: '1px solid #e0e0e0', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        fontWeight: 'bold', 
        fontSize: 12, 
        p: 1,
        color: '#6c757d'
      }}>
        Total
      </Box>
      {/* Value Traded - Foreign */}
      <Box sx={{ 
        gridRow: '3', 
        gridColumn: '5', 
        bgcolor: '#fff', 
        border: '1px solid #e0e0e0', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        fontWeight: 'bold', 
        fontSize: 12, 
        p: 1,
        color: '#6c757d'
      }}>
        Total
      </Box>
      {/* Ownership Value - Saudi Individuals */}
      <Box sx={{ 
        gridRow: '3', 
        gridColumn: '6', 
        bgcolor: '#fff', 
        border: '1px solid #e0e0e0', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        fontWeight: 'bold', 
        fontSize: 12, 
        p: 1,
        color: '#6c757d'
      }}>
        Individuals
      </Box>
      {/* Ownership Value - Saudi Institutions */}
      <Box sx={{ 
        gridRow: '3', 
        gridColumn: '7', 
        bgcolor: '#fff', 
        border: '1px solid #e0e0e0', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        fontWeight: 'bold', 
        fontSize: 12, 
        p: 1,
        color: '#6c757d'
      }}>
        Institutions
      </Box>
      {/* Ownership Value - GCC */}
      <Box sx={{ 
        gridRow: '3', 
        gridColumn: '8', 
        bgcolor: '#fff', 
        border: '1px solid #e0e0e0', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        fontWeight: 'bold', 
        fontSize: 12, 
        p: 1,
        color: '#6c757d'
      }}>
        Total
      </Box>
      {/* Ownership Value - Foreign */}
      <Box sx={{ 
        gridRow: '3', 
        gridColumn: '9', 
        bgcolor: '#fff', 
        border: '1px solid #e0e0e0', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        fontWeight: 'bold', 
        fontSize: 12, 
        p: 1,
        color: '#6c757d'
      }}>
        Total
      </Box>
    </Box>
  );

  // Map field names to column positions
  const getColumnValue = (row, fieldName) => {
    if (!row.data) return null;
    
    // Map the hierarchical structure to field names
    const fieldMap = {
      'DATE': row.data.DATE,
      'Saudi_ValueTraded_Individuals': row.data.Saudi_ValueTraded_Individuals,
      'Saudi_ValueTraded_Institutions': row.data.Saudi_ValueTraded_Institutions,
      'GCC_ValueTraded_Total': row.data.GCC_ValueTraded_Total,
      'Foreign_ValueTraded_Total': row.data.Foreign_ValueTraded_Total,
      'Saudi_OwnershipValue_Individuals': row.data.Saudi_OwnershipValue_Individuals,
      'Saudi_OwnershipValue_Institutions': row.data.Saudi_OwnershipValue_Institutions,
      'GCC_OwnershipValue_Total': row.data.GCC_OwnershipValue_Total,
      'Foreign_OwnershipValue_Total': row.data.Foreign_OwnershipValue_Total,
    };
    
    return fieldMap[fieldName] || null;
  };

  // Function to clean up failed uploads
  const cleanFailedUploads = () => {
    setPdfColumns(prev => prev.filter(col => col.data && !col.error));
  };

  // Function to clear all data
  const handleClearAllData = async () => {
    try {
      // Clear frontend state
      setPdfColumns([]);
      localStorage.removeItem('pdfColumns');
      
      // Clear backend CSV file
      const response = await fetch('http://localhost:5003/api/clear_data', {
        method: 'POST',
      });
      
      if (response.ok) {
        alert('تم مسح جميع البيانات بنجاح');
      } else {
        alert('تم مسح البيانات من الواجهة، لكن حدث خطأ في مسح ملف CSV');
      }
    } catch (error) {
      alert('تم مسح البيانات من الواجهة، لكن حدث خطأ في الاتصال بالخادم');
    }
    setShowClearConfirmation(false);
  };

  // Custom table with hierarchical header
  const renderHierarchicalTable = () => {

    
    // Filter out failed uploads for display
    const successfulColumns = pdfColumns.filter(col => col.data && !col.error);
    
    if (successfulColumns.length === 0) {
      return (
        <Paper elevation={4} sx={{ 
          maxWidth: '100%', 
          mx: 'auto', 
          mb: 2, 
          p: 4, 
          borderRadius: 4,
          boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
          bgcolor: '#fafafa'
        }}>
          <Typography variant="h5" sx={{ 
            mb: 3, 
            color: '#1e6641',
            fontWeight: 'bold',
            textAlign: 'center'
          }}>
            بيانات التداول والملكية
          </Typography>
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body1" sx={{ color: '#666' }}>
              لا توجد بيانات مستخرجة بعد. قم برفع ملفات PDF لبدء الاستخراج.
            </Typography>
          </Box>
        </Paper>
      );
    }
    
    const formatValue = (value) => {
      if (!value || value === "" || value === "null" || value === "undefined") {
        return <span style={{ color: '#b71c1c' }}>لايوجد</span>;
      }
      const numValue = parseFloat(value);
      if (!isNaN(numValue)) {
        const formatted = numValue.toLocaleString('en-US');
        const color = numValue < 0 ? '#d32f2f' : numValue > 0 ? '#2e7d32' : '#666';
        return <span style={{ color, fontWeight: 500 }}>{formatted}</span>;
      }
      return value;
    };

    return (
      <Paper elevation={4} sx={{ 
        maxWidth: '100%', 
        mx: 'auto', 
        mb: 2, 
        p: 4, 
        borderRadius: 4,
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
        bgcolor: '#fafafa'
      }}>
        <Typography variant="h5" sx={{ 
          mb: 3, 
          color: '#1e6641',
          fontWeight: 'bold',
          textAlign: 'center'
        }}>
          بيانات التداول والملكية
        </Typography>
        <Box sx={{ overflowX: 'auto' }}>
          {/* Hierarchical Header */}
          <HierarchicalHeader />
          
          {/* Data Rows */}
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: 'minmax(150px, 200px) repeat(8, minmax(120px, 1fr))', // Match header columns
            border: '1px solid #e0e0e0',
            borderTop: 'none',
            borderRadius: '0 0 8px 8px',
            overflow: 'hidden',
            width: '100%'
          }}>
            {successfulColumns.map((row, rowIdx) => (
              <React.Fragment key={rowIdx}>
                {/* Date */}
                <Box sx={{
                  gridColumn: '1',
                  bgcolor: rowIdx % 2 === 0 ? '#fff' : '#f8f9fa',
                  border: '1px solid #e0e0e0',
                  borderTop: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 600,
                  fontSize: 14,
                  p: 2,
                  minHeight: 60,
                  borderRight: '2px solid #e0e0e0',
                  color: '#495057'
                }}>
                  {row.data ? row.data.DATE : row.filename}
                </Box>
                
                {/* Data cells mapped to hierarchical structure */}
                {[
                  'Saudi_ValueTraded_Individuals',
                  'Saudi_ValueTraded_Institutions', 
                  'GCC_ValueTraded_Total',
                  'Foreign_ValueTraded_Total',
                  'Saudi_OwnershipValue_Individuals',
                  'Saudi_OwnershipValue_Institutions',
                  'GCC_OwnershipValue_Total',
                  'Foreign_OwnershipValue_Total'
                ].map((field, colIdx) => (
                  <Box key={colIdx} sx={{
                    gridColumn: colIdx + 2, // Adjust column index for data cells
                    bgcolor: rowIdx % 2 === 0 ? '#fff' : '#f8f9fa',
                    border: '1px solid #e0e0e0',
                    borderTop: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 14,
                    p: 2,
                    minHeight: 60,
                    fontWeight: 500
                  }}>
                    {row.data ? formatValue(getColumnValue(row, field)) : <span style={{ color: '#b71c1c' }}>{row.error || 'خطأ'}</span>}
                  </Box>
                ))}
              </React.Fragment>
            ))}
          </Box>
        </Box>
      </Paper>
    );
  };

  // Replace renderElegantDataGrid with renderHierarchicalTable
  const renderElegantDataGrid = () => renderHierarchicalTable();

  // Fetch archived snapshots
  useEffect(() => {
    setSnapshotsLoading(true);
            fetch('http://localhost:5003/api/ownership_snapshots')
      .then(res => res.json())
      .then(data => {
        setSnapshots(data);
        setSnapshotsLoading(false);
      })
      .catch(err => {
        setSnapshotsError('فشل في تحميل ملفات الفترات السابقة');
        setSnapshotsLoading(false);
      });
  }, []);

  // Fetch user exports
  useEffect(() => {
    setUserExportsLoading(true);
            fetch('http://localhost:5003/api/user_exports')
      .then(res => res.json())
      .then(data => {
        setUserExports(data);
        setUserExportsLoading(false);
      })
      .catch(err => {
        setUserExportsError('فشل في تحميل ملفات قام المستخدم بحفظها');
        setUserExportsLoading(false);
      });
  }, []);

  // In App(), define a function to update the row and attach it to window so the modal can call it
  useEffect(() => {
    window.updateRowAfterCorrection = (updated) => {
      setPdfColumns((prevColumns) => prevColumns.map(col => {
        if (col.filename && updated.filename && col.filename.toString() === updated.filename.toString()) {
          return {
            ...col,
            data: {
              ...col.data,
              [updated.field]: updated.value || '',
            },
            error: updated.error || '',
          };
        }
        return col;
      }));
    };
    return () => { window.updateRowAfterCorrection = undefined; };
  }, []);

  // Sort function to handle retained earnings properly
  // const sortByRetainedEarnings = (a, b) => {
  //   const aValue = parseFloat(a.retained_earnings) || 0;
  //   const bValue = parseFloat(b.retained_earnings) || 0;
  //   return bValue - aValue; // Sort in descending order (highest first)
  // };

  // const filteredRows = rows
  //   .filter(
  //     (row) =>
  //       (row.company_name && row.company_name.includes(search)) ||
  //       (row.symbol && row.symbol.includes(search))
  //   )
  //   .sort(sortByRetainedEarnings); // Sort by retained earnings

  return (
    <Box dir="rtl" sx={{ minHeight: "100vh", bgcolor: "#f4f6fa", fontFamily: "'Tajawal', 'Cairo', 'Noto Sans Arabic', sans-serif", display: 'flex', flexDirection: 'column' }}>
      {/* Main app container */}
      {/* Header with gradient */}
      <Box sx={{
        width: '100%',
        py: { xs: 4, md: 6 },
        px: 0,
        mb: 0,
        background: 'linear-gradient(135deg, #0d3b23 0%, #1e6641 100%)',
        boxShadow: '0 20px 60px rgba(30, 102, 65, 0.3)',
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        flexDirection: 'row',
        justifyContent: 'flex-start',
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: '-1px',
          left: '-1px',
          right: '-1px',
          height: '4px',
          background: 'linear-gradient(90deg, #0d3b23 0%, #1e6641 50%, #0d3b23 100%)',
          borderRadius: '6px 6px 0 0',
          zIndex: 1
        },
        '&::after': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '4px',
          background: 'linear-gradient(90deg, #1e6641 0%, #2d8a5c 50%, #1e6641 100%)',
          opacity: 0.8
        }
      }}>
        <img
          src="/sama-header.png"
          alt="Saudi Central Bank Logo"
          style={{
            height: '120px',
            width: 'auto',
            marginLeft: 0,
            marginRight: 0,
            display: 'block',
            flexShrink: 0,
            filter: 'drop-shadow(0 4px 16px rgba(0,0,0,0.15))',
            objectFit: 'contain',
            position: 'relative',
            zIndex: 1
          }}
        />
      </Box>
      {/* Title and subtitle below header */}
      <Box sx={{ 
        textAlign: 'right', 
        mt: { xs: 3, md: 4 }, 
        mb: { xs: 3, md: 4 }, 
        pr: { xs: 3, md: 8 },
        pl: { xs: 3, md: 8 }
      }}>
        <Typography variant="h2" fontWeight="bold" sx={{ 
          mb: 2, 
          fontSize: { xs: 28, md: 42 }, 
          background: 'linear-gradient(135deg, #0d3b23 0%, #1e6641 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          display: 'inline-block',
          lineHeight: 1.2
        }}>
          مستخرج بيانات التداول والملكية
        </Typography>
        <Box sx={{ 
          height: 6, 
          width: 160, 
          background: 'linear-gradient(135deg, #1e6641 0%, #2d8a5c 100%)',
          mr: 0, 
          ml: 'unset', 
          borderRadius: 3, 
          mb: 3,
          boxShadow: '0 4px 16px rgba(30, 102, 65, 0.3)'
        }} />
        <Typography variant="h5" sx={{ 
          color: '#374151', 
          fontSize: { xs: 16, md: 22 },
          fontWeight: 500,
          lineHeight: 1.4
        }}>
          استخراج وتحليل بيانات السوق للسياسة النقدية
        </Typography>
      </Box>

      {/* Main card */}
      <Paper elevation={0} sx={{
        maxWidth: '95%',
        mx: 'auto',
        p: { xs: 3, md: 6 },
        borderRadius: 6,
        boxShadow: '0 25px 80px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.02)',
        mb: 6,
        width: '100%',
        border: 'none',
        background: 'linear-gradient(135deg, #ffffff 0%, #fafbfc 100%)',
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: '-1px',
          left: '-1px',
          right: '-1px',
          height: '4px',
          background: 'linear-gradient(90deg, #0d3b23 0%, #1e6641 50%, #0d3b23 100%)',
          borderRadius: '6px 6px 0 0',
          zIndex: 1
        }
      }}>
        {/* Upload and actions area */}
        <Box sx={{
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
          alignItems: { xs: 'stretch', md: 'center' },
          justifyContent: 'space-between',
          background: 'linear-gradient(135deg, #f0f9f0 0%, #e6f4e6 100%)',
          p: { xs: 4, md: 6 },
          mb: 6,
          borderRadius: 4,
          gap: { xs: 3, md: 0 },
          border: '1px solid #d1f2d1',
          boxShadow: '0 8px 32px rgba(30, 102, 65, 0.12)',
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: '-1px',
            left: '-1px',
            right: '-1px',
            height: '3px',
            background: 'linear-gradient(90deg, #1e6641 0%, #2d8a5c 100%)',
            borderRadius: '4px 4px 0 0',
            zIndex: 1
          }
        }}>
          {/* PDF Upload section in the right corner */}
          <Box sx={{ 
            minWidth: { xs: '100%', md: 380 }, 
            maxWidth: { xs: '100%', md: 450 }, 
            width: '100%', 
            textAlign: 'right' 
          }}>
            <input
              accept=".pdf"
              style={{ display: 'none' }}
              id="pdf-upload"
              multiple
              type="file"
              onChange={handleFileSelection}
            />
            <label htmlFor="pdf-upload">
              <Button
                variant="contained"
                component="span"
                disabled={uploading}
                fullWidth
                startIcon={<CloudUploadIcon sx={{ fontSize: 22 }} />}
                className="arabic-text"
                sx={{ 
                  background: 'linear-gradient(135deg, #1e6641 0%, #2d8a5c 100%)',
                  '&:hover': { 
                    background: 'linear-gradient(135deg, #14532d 0%, #1e6641 100%)',
                    transform: 'translateY(-2px)',
                    boxShadow: '0 12px 24px rgba(30, 102, 65, 0.3)'
                  }, 
                  py: 2, 
                  px: 4,
                  fontSize: 16,
                  height: 56,
                  borderRadius: 4,
                  fontWeight: 600,
                  textTransform: 'none',
                  boxShadow: '0 8px 24px rgba(30, 102, 65, 0.25)',
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  fontFamily: '"Noto Sans Arabic", "Segoe UI", "Tahoma", "Arial", sans-serif',
                  letterSpacing: '0.5px',
                  direction: 'rtl',
                  textAlign: 'center',
                  lineHeight: 1.2,
                  '& .MuiButton-startIcon': {
                    marginRight: '20px'
                  },
                  '&:disabled': {
                    background: '#9ca3af',
                    transform: 'none',
                    boxShadow: 'none'
                  }
                }}
              >
                {uploading ? 'جاري رفع الملفات...' : selectedFiles.length > 0 ? `رفع ${selectedFiles.length} ملف` : 'رفع ملفات PDF'}
              </Button>
            </label>
            {uploading && (
              <Box sx={{ 
                mt: 2,
                p: 2,
                background: 'rgba(30, 102, 65, 0.08)',
                borderRadius: 2,
                border: '1px solid rgba(30, 102, 65, 0.15)',
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                gap: 1.5
              }}>
                <CircularProgress size={18} sx={{ 
                  color: '#1e6641',
                  '& .MuiCircularProgress-circle': {
                    strokeLinecap: 'round',
                  }
                }} />
                <Typography variant="body2" sx={{ 
                  color: '#1e6641', 
                  fontWeight: 500,
                  fontSize: 14
                }}>
                  جاري معالجة الملفات...
                </Typography>
              </Box>
            )}
            {selectedFiles.length > 0 && !uploading && (
              <Typography variant="caption" sx={{ 
                color: '#1e6641', 
                fontSize: 13, 
                mt: 2, 
                display: 'block',
                textAlign: 'center',
                fontWeight: 600,
                bgcolor: '#f0f9f0',
                py: 1,
                px: 2,
                borderRadius: 2,
                border: '1px solid #d1f2d1'
              }}>
                {selectedFiles.length} ملف محدد
              </Typography>
            )}
            
            {/* Selected Files Summary */}
            {selectedFiles.length > 0 && !uploading && !showUploadConfirmation && (
              <Box sx={{ 
                mt: 3, 
                p: 3, 
                bgcolor: '#ffffff', 
                borderRadius: 3, 
                border: '1px solid #d1f2d1',
                boxShadow: '0 4px 20px rgba(30, 102, 65, 0.08)',
                maxHeight: 200,
                overflowY: 'auto'
              }}>
                <Box sx={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  mb: 2
                }}>
                  <Typography variant="body2" sx={{ 
                    color: '#1e6641', 
                    fontWeight: 700,
                    fontSize: 14
                  }}>
                    الملفات المحددة: ({selectedFiles.length})
                  </Typography>
                  <Button
                    variant="text"
                    size="small"
                    onClick={() => setSelectedFiles([])}
                    sx={{
                      color: '#dc2626',
                      fontSize: 12,
                      fontWeight: 600,
                      p: 1,
                      minWidth: 'auto',
                      borderRadius: 2,
                      '&:hover': {
                        backgroundColor: '#fef2f2',
                        color: '#b91c1c'
                      }
                    }}
                  >
                    مسح الكل
                  </Button>
                </Box>
                {selectedFiles.map((file, index) => (
                  <Box key={index} sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between',
                    mb: 1.5,
                    p: 1.5,
                    bgcolor: '#f9fafb',
                    borderRadius: 2,
                    border: '1px solid #e5e7eb',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      borderColor: '#1e6641',
                      boxShadow: '0 2px 8px rgba(30, 102, 65, 0.15)',
                      bgcolor: '#f0f9f0'
                    }
                  }}>
                    <Box sx={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      flex: 1,
                      minWidth: 0
                    }}>
                      <Box sx={{
                        width: 28,
                        height: 28,
                        borderRadius: 2,
                        background: 'linear-gradient(135deg, #1e6641 0%, #2d8a5c 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        mr: 1.5,
                        flexShrink: 0,
                        boxShadow: '0 2px 8px rgba(30, 102, 65, 0.2)'
                      }}>
                        <Typography sx={{ 
                          color: 'white', 
                          fontSize: 12, 
                          fontWeight: 'bold' 
                        }}>
                          {index + 1}
                        </Typography>
                      </Box>
                      <Box sx={{ minWidth: 0, flex: 1 }}>
                        <Typography variant="body2" sx={{ 
                          color: '#111827',
                          fontSize: 12,
                          fontWeight: 600,
                          display: 'block',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          mb: 0.5
                        }}>
                          {file.name}
                        </Typography>
                        <Typography variant="caption" sx={{ 
                          color: '#6b7280',
                          fontSize: 11,
                          bgcolor: '#f3f4f6',
                          px: 1.5,
                          py: 0.5,
                          borderRadius: 1,
                          fontWeight: 500
                        }}>
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </Typography>
                      </Box>
                    </Box>
                    <IconButton
                      size="small"
                      onClick={() => {
                        setSelectedFiles(prev => prev.filter((_, i) => i !== index));
                      }}
                      sx={{
                        color: '#dc2626',
                        p: 0.5,
                        ml: 1,
                        '&:hover': {
                          backgroundColor: '#fef2f2',
                          color: '#b91c1c',
                          transform: 'scale(1.1)'
                        },
                        transition: 'all 0.2s ease-in-out'
                      }}
                    >
                      <CloseIcon sx={{ fontSize: 16 }} />
                    </IconButton>
                  </Box>
                ))}
                <Box sx={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'center',
                  mt: 3,
                  pt: 2,
                  borderTop: '1px solid #e5e7eb'
                }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setSelectedFiles([])}
                    sx={{
                      color: '#6b7280',
                      borderColor: '#d1d5db',
                      fontSize: 12,
                      py: 1,
                      px: 2.5,
                      borderRadius: 2,
                      fontWeight: 600,
                      '&:hover': {
                        borderColor: '#9ca3af',
                        backgroundColor: '#f9fafb',
                        color: '#374151'
                      }
                    }}
                  >
                    إلغاء التحديد
                  </Button>
                  <Button
                    variant="contained"
                    size="small"
                    onClick={() => setShowUploadConfirmation(true)}
                    sx={{
                      background: 'linear-gradient(135deg, #1e6641 0%, #2d8a5c 100%)',
                      fontSize: 12,
                      fontWeight: 700,
                      py: 1,
                      px: 3,
                      borderRadius: 2,
                      boxShadow: '0 4px 12px rgba(30, 102, 65, 0.25)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #14532d 0%, #1e6641 100%)',
                        transform: 'translateY(-1px)',
                        boxShadow: '0 6px 16px rgba(30, 102, 65, 0.35)'
                      }
                    }}
                  >
                    تأكيد الرفع →
                  </Button>
                </Box>
              </Box>
            )}
          </Box>
                           {/* Action buttons in the left corner */}
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: { xs: 'flex-start', md: 'flex-end' }, 
            width: { xs: '100%', md: 'auto' }, 
            height: '100%', 
            gap: 3 
          }}>
                   {/* Clear All Data Button */}
                   <Tooltip title="مسح جميع البيانات" arrow placement="top">
                     <IconButton
                       onClick={() => setShowClearConfirmation(true)}
                       sx={{
                         width: 56,
                         height: 56,
                         borderRadius: 3,
                         bgcolor: '#f8f9fa',
                         color: '#6c757d',
                         border: '1px solid #dee2e6',
                         '&:hover': {
                           bgcolor: '#e9ecef',
                           borderColor: '#ced4da',
                           color: '#495057',
                           transform: 'translateY(-2px)',
                         },
                         boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                         '&:hover': {
                           boxShadow: '0 8px 20px rgba(0,0,0,0.12)',
                         },
                         transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                       }}
                     >
                       <DeleteForeverIcon sx={{ fontSize: 22 }} />
                     </IconButton>
                   </Tooltip>
                   
            {/* Secondary Reset Button */}
                   <Tooltip title="إعادة تعيين" arrow placement="top">
                     <IconButton
              onClick={handleReset}
              sx={{
                         width: 56,
                height: 56,
                borderRadius: 3,
                bgcolor: '#f8f9fa',
                color: '#6c757d',
                border: '1px solid #dee2e6',
                '&:hover': {
                  bgcolor: '#e9ecef',
                  borderColor: '#ced4da',
                  transform: 'translateY(-2px)',
                },
                boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                '&:hover': {
                  boxShadow: '0 8px 20px rgba(0,0,0,0.12)',
                },
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
              }}
            >
                       <RefreshIcon sx={{ fontSize: 22, color: '#6c757d' }} />
                     </IconButton>
                   </Tooltip>
            
            {/* Primary Download Button */}
            <Tooltip title="تصدير الجدول إلى Excel" arrow placement="top">
              <Button
                variant="contained"
                onClick={handleExcelExport}
                sx={{
                  minWidth: 180,
                  height: 56,
                  px: 5,
                  py: 2,
                  borderRadius: 4,
                  background: 'linear-gradient(135deg, #1e6641 0%, #2d8a5c 100%)',
                  color: 'white',
                  fontWeight: 700,
                  fontSize: 15,
                  textTransform: 'none',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #14532d 0%, #1e6641 100%)',
                    transform: 'translateY(-2px)',
                  },
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                  boxShadow: '0 8px 24px rgba(30, 102, 65, 0.25)',
                  '&:hover': {
                    boxShadow: '0 12px 32px rgba(30, 102, 65, 0.35)',
                  },
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                }}
              >
                <FileDownloadIcon sx={{ fontSize: 20, color: 'white' }} />
                تصدير الجدول
              </Button>
            </Tooltip>
          </Box>
        </Box>
        

        
        {/* PDF Data Table */}
        {renderElegantDataGrid()}
        
        {/* Upload Results Section */}
        {uploadResults.length > 0 && (
          <Paper elevation={4} sx={{ maxWidth: 1800, mx: 'auto', mb: 2, p: 3, borderRadius: 4 }}>
            <Typography variant="h5" sx={{ mb: 2, color: '#1e6641' }}>نتائج رفع الملفات</Typography>
            {uploadResults.map((result, idx) => (
              <Box key={idx} sx={{ mb: 2, p: 2, border: '1px solid #e0e0e0', borderRadius: 2 }}>
                <Typography variant="h6" sx={{ mb: 1 }}>{result.filename}</Typography>
                {result.success ? (
                  <Box>
                    <Typography sx={{ mb: 1 }}>الأرباح المبقاة: {result.value ? parseFloat(result.value).toLocaleString() : ''} ريال</Typography>
                    {result.screenshot_path && (
                      <Box sx={{ mt: 1 }}>
                        <img src={`http://localhost:5003${result.screenshot_path}`} alt="Evidence" style={{ maxWidth: '100%', maxHeight: '200px', border: '1px solid #ccc', borderRadius: 4 }} />
                      </Box>
                    )}
                  </Box>
                ) : (
                  <Alert severity="error">{result.error || 'فشل في الاستخراج'}</Alert>
                )}
              </Box>
            ))}
          </Paper>
        )}
      </Paper>
      
      {/* Evidence Modal */}
      <EvidenceModal
        open={evidenceModalOpen}
        onClose={() => setEvidenceModalOpen(false)}
        evidenceData={evidenceData}
        loading={evidenceLoading}
        error={evidenceError}
      />
      
      {/* Footer */}
      <Box sx={{ 
        textAlign: 'center', 
        color: '#64748b', 
        py: 4, 
        fontSize: 16, 
        mt: 'auto',
        borderTop: '1px solid #e2e8f0',
        background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)'
      }}>
        <Typography variant="body1" sx={{ 
          fontWeight: 500,
          color: '#475569'
        }}>
          © {new Date().getFullYear()} مركز الابتكار
        </Typography>
        <Typography variant="caption" sx={{ 
          display: 'block',
          mt: 1,
          color: '#94a3b8',
          fontSize: 13
        }}>
          نظام استخراج بيانات التداول والملكية
        </Typography>
      </Box>
      {/* Upload confirmation dialog */}
      <Dialog 
        open={showUploadConfirmation} 
        onClose={cancelUpload} 
        maxWidth="md" 
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 6,
            boxShadow: '0 32px 80px rgba(0,0,0,0.12)',
            border: 'none',
            overflow: 'hidden',
            maxHeight: '90vh'
          }
        }}
      >
        <Box sx={{ 
          background: 'linear-gradient(135deg, #0d3b23 0%, #1e6641 100%)',
          p: 4,
          textAlign: 'center',
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'url("data:image/svg+xml,%3Csvg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"%3E%3Cg fill="none" fill-rule="evenodd"%3E%3Cg fill="%23ffffff" fill-opacity="0.05"%3E%3Ccircle cx="30" cy="30" r="2"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
            opacity: 0.3
          }
        }}>
          <Typography sx={{ 
            fontWeight: 800, 
            color: 'white', 
            fontSize: { xs: 20, md: 28 },
            mb: 1,
            position: 'relative',
            zIndex: 1
          }}>
            تأكيد رفع الملفات
          </Typography>
          <Typography sx={{ 
            color: 'rgba(255,255,255,0.95)', 
            fontSize: { xs: 14, md: 16 },
            position: 'relative',
            zIndex: 1
          }}>
            هل أنت متأكد من رفع الملفات التالية؟
          </Typography>
        </Box>
        
        <DialogContent sx={{ p: { xs: 3, md: 5 } }}>
          {/* Add More Files Button */}
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            mb: 4 
          }}>
            <input
              accept=".pdf"
              style={{ display: 'none' }}
              id="add-more-files"
              multiple
              type="file"
              onChange={(event) => {
                const newFiles = Array.from(event.target.files);
                if (newFiles.length > 0) {
                  // Check for duplicate files
                  const duplicates = newFiles.filter(file => 
                    selectedFiles.some(existingFile => existingFile.name === file.name)
                  );
                  
                  if (duplicates.length > 0) {
                    const duplicateNames = duplicates.map(f => f.name).join(', ');
                    alert(`الملفات التالية موجودة مسبقاً: ${duplicateNames}`);
                    return;
                  }
                  
                  // Check for non-PDF files
                  const nonPdfFiles = newFiles.filter(file => file.type !== 'application/pdf');
                  if (nonPdfFiles.length > 0) {
                    const nonPdfNames = nonPdfFiles.map(f => f.name).join(', ');
                    alert(`الملفات التالية ليست ملفات PDF: ${nonPdfNames}`);
                    return;
                  }
                  
                  setSelectedFiles(prev => [...prev, ...newFiles]);
                }
                // Reset the input value so the same file can be selected again
                event.target.value = '';
              }}
            />
            <label htmlFor="add-more-files">
              <Button
                variant="outlined"
                component="span"
                startIcon={<CloudUploadIcon sx={{ fontSize: 20 }} />}
                sx={{
                  borderColor: '#1e6641',
                  color: '#1e6641',
                  borderWidth: 2,
                  py: 2,
                  px: 4,
                  borderRadius: 4,
                  fontWeight: 700,
                  fontSize: 15,
                  textTransform: 'none',
                  '&:hover': {
                    borderColor: '#14532d',
                    backgroundColor: '#f0f9f0',
                    transform: 'translateY(-2px)',
                    boxShadow: '0 8px 20px rgba(30, 102, 65, 0.2)'
                  },
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  boxShadow: '0 4px 16px rgba(30, 102, 65, 0.15)',
                  '&:hover': {
                    boxShadow: '0 8px 24px rgba(30, 102, 65, 0.25)',
                  }
                }}
              >
                + إضافة ملفات أخرى
              </Button>
            </label>
          </Box>
          
          {/* File Management Header */}
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            mb: 3,
            p: 3,
            bgcolor: '#f8fafc',
            borderRadius: 3,
            border: '1px solid #e2e8f0'
          }}>
            <Typography variant="h6" sx={{ 
              color: '#0f172a', 
              fontWeight: 700,
              fontSize: 18
            }}>
              الملفات المحددة ({selectedFiles.length})
            </Typography>
            <Button
              variant="text"
              onClick={() => setSelectedFiles([])}
              sx={{
                color: '#dc2626',
                fontSize: 14,
                fontWeight: 700,
                '&:hover': {
                  backgroundColor: '#fef2f2',
                  color: '#b91c1c'
                }
              }}
            >
              مسح الكل
            </Button>
          </Box>
          
          <Box sx={{ 
            maxHeight: 400, 
            overflowY: 'auto', 
            bgcolor: '#ffffff', 
            p: 4, 
            borderRadius: 4,
            border: '1px solid #e2e8f0',
            mb: 4,
            boxShadow: '0 4px 20px rgba(0,0,0,0.04)'
          }}>
            {selectedFiles.map((file, index) => (
              <Box key={index} sx={{ 
                display: 'flex',
                alignItems: 'center',
                p: 3, 
                mb: 2, 
                bgcolor: '#f8fafc', 
                borderRadius: 4,
                border: '1px solid #e2e8f0',
                boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                '&:hover': {
                  boxShadow: '0 8px 24px rgba(0,0,0,0.08)',
                  transform: 'translateY(-2px)',
                  borderColor: '#1e6641',
                  bgcolor: '#f0f9f0'
                }
              }}>
                <Box sx={{
                  width: 48,
                  height: 48,
                  borderRadius: 3,
                  background: 'linear-gradient(135deg, #1e6641 0%, #2d8a5c 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mr: 3,
                  flexShrink: 0,
                  boxShadow: '0 4px 16px rgba(30, 102, 65, 0.2)'
                }}>
                  <Typography sx={{ 
                    color: 'white', 
                    fontSize: 18, 
                    fontWeight: 'bold' 
                  }}>
                    {index + 1}
                  </Typography>
                </Box>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="body1" sx={{ 
                    fontWeight: 700, 
                    color: '#0f172a',
                    mb: 1,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    fontSize: 15
                  }}>
                    {file.name}
                  </Typography>
                  <Typography variant="body2" sx={{ 
                    color: '#64748b',
                    bgcolor: '#f1f5f9',
                    px: 2,
                    py: 1,
                    borderRadius: 2,
                    fontSize: 13,
                    fontWeight: 600,
                    display: 'inline-block'
                  }}>
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </Typography>
                </Box>
                {/* Remove file button */}
                <IconButton
                  onClick={() => {
                    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
                  }}
                  sx={{
                    color: '#dc2626',
                    ml: 2,
                    width: 40,
                    height: 40,
                    '&:hover': {
                      backgroundColor: '#fef2f2',
                      color: '#b91c1c',
                      transform: 'scale(1.1)'
                    },
                    transition: 'all 0.2s ease-in-out'
                  }}
                >
                  <CloseIcon sx={{ fontSize: 20 }} />
                </IconButton>
              </Box>
            ))}
            
            {selectedFiles.length === 0 && (
              <Box sx={{ 
                textAlign: 'center', 
                py: 6, 
                color: '#94a3b8',
                fontStyle: 'italic'
              }}>
                <CloudUploadIcon sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
                <Typography variant="h6" sx={{ color: '#64748b', mb: 1 }}>
                  لا توجد ملفات محددة
                </Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8' }}>
                  قم بتحديد ملفات PDF للرفع
                </Typography>
              </Box>
            )}
          </Box>
          
          <Box sx={{
            bgcolor: '#f0f9f0',
            p: 4,
            borderRadius: 4,
            border: '1px solid #d1f2d1',
            textAlign: 'center',
            position: 'relative',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '3px',
              background: 'linear-gradient(90deg, #1e6641 0%, #2d8a5c 100%)',
              borderRadius: '4px 4px 0 0'
            }
          }}>
            <Typography variant="body1" sx={{ 
              color: '#1e6641',
              fontSize: 15,
              lineHeight: 1.6,
              fontWeight: 600,
              mb: 2
            }}>
              سيتم استخراج البيانات المالية من هذه الملفات وعرضها في الجدول
            </Typography>
            <Typography variant="body2" sx={{ 
              color: '#1e6641',
              fontSize: 14,
              display: 'block',
              fontWeight: 500,
              bgcolor: '#f0f9f0',
              py: 1.5,
              px: 3,
              borderRadius: 3,
              border: '1px solid #d1f2d1',
              display: 'inline-block'
            }}>
              إجمالي الملفات: {selectedFiles.length} ملف
            </Typography>
          </Box>
        </DialogContent>
        
        <DialogActions sx={{ 
          justifyContent: 'center',
          pb: 5, 
          px: 5,
          gap: 3
        }}>
          <Button 
            onClick={cancelUpload} 
            variant="outlined"
            sx={{
              color: '#64748b', 
              borderColor: '#cbd5e1',
              minWidth: 140,
              py: 1.5,
              px: 4,
              borderRadius: 3,
              fontWeight: 700,
              fontSize: 15,
              textTransform: 'none',
              borderWidth: 2,
              '&:hover': { 
                bgcolor: '#f8fafc',
                borderColor: '#94a3b8',
                color: '#475569'
              }
            }}
          >
            إلغاء
          </Button>
          <Button 
            onClick={handleFileUpload} 
            variant="contained"
            disabled={uploading || selectedFiles.length === 0}
            sx={{
              background: 'linear-gradient(135deg, #1e6641 0%, #2d8a5c 100%)',
              minWidth: 160,
              py: 1.5,
              px: 4,
              borderRadius: 3,
              fontWeight: 700,
              fontSize: 15,
              textTransform: 'none',
              boxShadow: '0 8px 24px rgba(30, 102, 65, 0.3)',
              '&:hover': { 
                background: 'linear-gradient(135deg, #14532d 0%, #1e6641 100%)',
                boxShadow: '0 12px 32px rgba(30, 102, 65, 0.4)',
                transform: 'translateY(-2px)'
              },
              '&:disabled': {
                background: '#9ca3af',
                boxShadow: 'none',
                transform: 'none'
              },
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
            }}
          >
            {uploading ? 'جاري الرفع...' : `تأكيد الرفع (${selectedFiles.length})`}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete confirmation dialog */}
      <Dialog open={deleteDialogOpen} onClose={cancelDeleteExport}>
        <DialogTitle sx={{ fontWeight: 700, color: '#1e6641' }}>تأكيد الحذف</DialogTitle>
        <DialogContent>
          <Typography>هل أنت متأكد أنك تريد حذف هذا الملف؟ لا يمكن التراجع عن هذه العملية.</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={cancelDeleteExport} sx={{ color: '#37474f' }}>إلغاء</Button>
          <Button onClick={confirmDeleteExport} sx={{ color: '#b71c1c', fontWeight: 700 }}>حذف</Button>
        </DialogActions>
      </Dialog>

      {/* Clear all data confirmation dialog */}
      <Dialog 
        open={showClearConfirmation} 
        onClose={() => setShowClearConfirmation(false)} 
        maxWidth="xs" 
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
            border: 'none'
          }
        }}
      >
        <DialogTitle sx={{ 
          pb: 2, 
          textAlign: 'center',
          borderBottom: '1px solid #f0f0f0'
        }}>
          <Typography variant="h6" sx={{ 
            fontWeight: 600, 
            color: '#2c3e50',
            fontSize: '1.1rem'
          }}>
            مسح جميع البيانات
          </Typography>
        </DialogTitle>
        
        <DialogContent sx={{ pt: 3, pb: 2, textAlign: 'center' }}>
          <Typography variant="body1" sx={{ 
            color: '#5a6c7d', 
            lineHeight: 1.6,
            fontSize: '0.95rem'
          }}>
            سيتم حذف جميع البيانات المحفوظة نهائياً
          </Typography>
        </DialogContent>
        
        <DialogActions sx={{ 
          px: 3, 
          pb: 3, 
          justifyContent: 'center',
          gap: 2
        }}>
          <Button 
            onClick={() => setShowClearConfirmation(false)} 
            variant="outlined" 
            sx={{ 
              minWidth: 100,
              borderColor: '#d1d5db',
              color: '#6b7280',
              '&:hover': {
                borderColor: '#9ca3af',
                backgroundColor: '#f9fafb'
              }
            }}
          >
            إلغاء
          </Button>
          <Button 
            onClick={handleClearAllData} 
            variant="contained" 
            sx={{ 
              minWidth: 100,
              backgroundColor: '#ef4444',
              '&:hover': {
                backgroundColor: '#dc2626'
              }
            }}
          >
            مسح
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default App;
