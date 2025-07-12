import React, { useState, useEffect } from "react";
import { DataGrid } from "@mui/x-data-grid";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Paper from "@mui/material/Paper";
import RefreshIcon from "@mui/icons-material/Refresh";
import Typography from "@mui/material/Typography";
import Papa from "papaparse";

const columns = [
  { field: "symbol", headerName: "رمز الشركة", width: 120, align: "right", headerAlign: "right" },
  { field: "company_name", headerName: "الشركة", width: 180, align: "right", headerAlign: "right" },
  { field: "foreign_ownership", headerName: "ملكية جميع المستثمرين الأجانب", width: 200, align: "right", headerAlign: "right" },
  { field: "max_allowed", headerName: "الحد الأعلى", width: 150, align: "right", headerAlign: "right" },
  { field: "investor_limit", headerName: "ملكية المستثمر الاستراتيجي الأجنبي", width: 180, align: "right", headerAlign: "right" },
  { 
    field: "retained_earnings", 
    headerName: "الأرباح المبقاة", 
    width: 180, 
    align: "right", 
    headerAlign: "right",
    renderCell: (params) => {
      const value = params.value;
      if (!value || value === "" || value === "null" || value === "undefined") {
        return "لايوجد";
      }
      const numValue = parseFloat(value);
      if (!isNaN(numValue)) {
        return numValue.toLocaleString('en-US'); // English numerals
      }
      return value;
    }
  },
  { 
    field: "reinvested_earnings", 
    headerName: "الأرباح المعاد استثمارها", 
    width: 200, 
    align: "right", 
    headerAlign: "right",
    renderCell: (params) => {
      const value = params.value;
      if (!value || value === "" || value === "null" || value === "undefined") {
        return "لايوجد";
      }
      const numValue = parseFloat(value);
      if (!isNaN(numValue)) {
        return numValue.toLocaleString('en-US'); // English numerals
      }
      return value;
    }
  },
];

function App() {
  const [rows, setRows] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchData = () => {
    setLoading(true);
    
    // Load foreign ownership data (JSON)
    const loadForeignOwnership = fetch("/foreign_ownership_data.json")
      .then((res) => res.json())
      .catch((error) => {
        console.error("Error loading foreign ownership data:", error);
        return [];
      });

    // Load reinvested earnings data (CSV)
    const loadReinvestedEarnings = new Promise((resolve) => {
      Papa.parse("/reinvested_earnings_results.csv", {
        download: true,
        header: true,
        complete: (result) => {
          console.log("CSV parsing result:", result);
          if (result.data && result.data.length > 0) {
            // Clean and process CSV data
            const cleanedData = result.data
              .filter(row => row.company_symbol && row.company_symbol.trim() !== '')
              .map((row) => {
                const cleanedRow = {};
                Object.keys(row).forEach(key => {
                  const cleanKey = key.trim();
                  cleanedRow[cleanKey] = row[key] ? row[key].trim() : '';
                });
                return cleanedRow;
              });
            console.log("Cleaned CSV data:", cleanedData);
            resolve(cleanedData);
          } else {
            console.log("No CSV data found");
            resolve([]);
          }
        },
        error: (error) => {
          console.error("Error loading reinvested earnings data:", error);
          resolve([]);
        }
      });
    });

    // Combine both datasets
    Promise.all([loadForeignOwnership, loadReinvestedEarnings])
      .then(([foreignOwnershipData, reinvestedEarningsData]) => {
        console.log("Foreign ownership data count:", foreignOwnershipData.length);
        console.log("Reinvested earnings data count:", reinvestedEarningsData.length);
        
        // Create a map of reinvested earnings data by symbol
        const earningsMap = {};
        
        reinvestedEarningsData.forEach(row => {
          const symbol = row.company_symbol ? row.company_symbol.toString().trim() : "";
          if (symbol) {
            earningsMap[symbol] = {
              retained_earnings: row.retained_earnings || "",
              reinvested_earnings: row.reinvested_earnings || "",
              year: row.year || "",
              error: row.error || ""
            };
            console.log(`Mapped earnings for ${symbol}:`, earningsMap[symbol]);
          }
        });

        console.log("Earnings map keys:", Object.keys(earningsMap));
        console.log("Sample earnings data for 2010:", earningsMap["2010"]);
        console.log("Sample earnings data for 1050:", earningsMap["1050"]);

        // Merge the data
        const mergedData = foreignOwnershipData.map((row, idx) => {
          const symbol = row.symbol ? row.symbol.toString().trim() : "";
          const earningsData = earningsMap[symbol] || {};
          const hasEarningsData = symbol in earningsMap;
          
          if (hasEarningsData) {
            console.log(`Found earnings data for ${symbol}:`, earningsData);
          }
          
          const mergedRow = {
            ...row,
            retained_earnings: earningsData.retained_earnings || "",
            reinvested_earnings: earningsData.reinvested_earnings || "",
            year: earningsData.year || "",
            error: earningsData.error || "",
            id: symbol + idx,
          };
          
          // Debug: Log first few rows to see the data structure
          if (idx < 5 || symbol === "2010") {
            console.log(`Row ${idx} (${symbol}):`, {
              symbol: mergedRow.symbol,
              company_name: mergedRow.company_name,
              retained_earnings: mergedRow.retained_earnings,
              reinvested_earnings: mergedRow.reinvested_earnings
            });
          }
          
          return mergedRow;
        });

        console.log("Final merged data sample:", mergedData.slice(0, 3));
        setRows(mergedData);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error combining data:", error);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredRows = rows.filter(
    (row) =>
      (row.company_name && row.company_name.includes(search)) ||
      (row.symbol && row.symbol.includes(search))
  );

  return (
    <Box dir="rtl" sx={{ minHeight: "100vh", bgcolor: "#f4f6fa", fontFamily: "'Tajawal', 'Cairo', 'Noto Sans Arabic', sans-serif", display: 'flex', flexDirection: 'column' }}>
      {/* Header with gradient */}
      <Box sx={{
        width: '100%',
        py: { xs: 3, md: 4 },
        px: 0,
        mb: 0,
        background: 'linear-gradient(90deg, #0d3b23 0%, #1e6641 100%)',
        boxShadow: '0 6px 24px 0 rgba(20, 83, 45, 0.18)',
        borderBottom: '4px solid #14532d',
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        flexDirection: 'row', // logo on the right for RTL
        justifyContent: 'flex-start',
      }}>
        <img
          src="/sama-header.png"
          alt="Saudi Central Bank Logo"
          style={{
            height: '96px',
            width: 'auto',
            marginLeft: 0,
            marginRight: 0,
            display: 'block',
            flexShrink: 0,
            filter: 'drop-shadow(0 2px 8px rgba(0,0,0,0.08))',
            objectFit: 'contain',
          }}
        />
      </Box>
      {/* Title and subtitle below header */}
      <Box sx={{ textAlign: 'right', mt: { xs: 3, md: 5 }, mb: { xs: 3, md: 5 }, pr: { xs: 2, md: 8 } }}>
        <Typography variant="h3" fontWeight="bold" sx={{ mb: 1, fontSize: { xs: 26, md: 36 }, color: '#1e6641', display: 'inline-block' }}>
          جدول ملكية الأجانب والأرباح المبقاة
        </Typography>
        <Box sx={{ height: 4, width: 120, bgcolor: '#1e6641', mr: 0, ml: 'unset', borderRadius: 2, mb: 2 }} />
        <Typography variant="subtitle1" sx={{ color: '#37474f', fontSize: { xs: 15, md: 20 } }}>
          بيانات محدثة من تداول السعودية - ملكية الأجانب والأرباح المبقاة في الشركات المدرجة
        </Typography>
      </Box>
      {/* Main card */}
      <Paper elevation={4} sx={{
        maxWidth: 1200,
        mx: 'auto',
        p: { xs: 2, md: 4 },
        borderRadius: 4,
        boxShadow: '0 6px 32px 0 rgba(30,102,65,0.10)',
        mb: 4,
        width: '100%',
      }}>
        {/* Search/filter area styled like the provided image */}
        <Box sx={{
          display: 'flex',
          flexDirection: { xs: 'column', md: 'row' },
          alignItems: { xs: 'stretch', md: 'center' },
          justifyContent: 'space-between',
          bgcolor: '#f3f4f6',
          p: 3,
          mb: 3,
          borderRadius: 2,
          gap: { xs: 2, md: 0 },
        }}>
          {/* Search box in the right corner */}
          <Box sx={{ minWidth: 320, maxWidth: 400, width: '100%', textAlign: 'right' }}>
            <Typography sx={{ mb: 1, fontWeight: 'bold', color: '#37474f', fontSize: 18 }}>
              رمز / شركة بحث
            </Typography>
            <TextField
              fullWidth
              placeholder="رمز / شركة بحث"
              variant="outlined"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              sx={{ bgcolor: 'white' }}
              inputProps={{ style: { textAlign: 'right' } }}
            />
          </Box>
          {/* Reset button in the left corner */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: { xs: 'flex-start', md: 'flex-end' }, width: { xs: '100%', md: 'auto' }, height: '100%' }}>
            <Button
              variant="outlined"
              color="success"
              onClick={fetchData}
              sx={{
                minWidth: 160,
                fontWeight: 'bold',
                fontSize: 18,
                height: 56,
                borderWidth: 2,
                borderColor: '#1e6641',
                color: '#1e6641',
                '&:hover': {
                  borderColor: '#1e6641',
                  background: '#e8f5ee',
                },
                display: 'flex',
                flexDirection: 'row',
                alignItems: 'center',
              }}
            >
              إعادة تعيين
              <RefreshIcon sx={{ ml: 1, fontSize: 32 }} />
            </Button>
          </Box>
        </Box>
        <DataGrid
          rows={filteredRows}
          columns={columns}
          pageSize={20}
          loading={loading}
          sx={{
            bgcolor: "white",
            fontFamily: "'Tajawal', 'Cairo', 'Noto Sans Arabic', sans-serif",
            direction: "rtl",
            borderRadius: 4, // more rounded corners
            fontSize: 18,
            boxShadow: '0 2px 16px 0 rgba(30,102,65,0.08)',
            border: 'none',
            "& .MuiDataGrid-columnHeaders": {
              bgcolor: "#e3ecfa",
              fontWeight: "bold",
              fontSize: 18,
              position: 'sticky',
              top: 0,
              zIndex: 1,
              direction: 'rtl',
              textAlign: 'right',
              boxShadow: '0 2px 8px 0 rgba(30,102,65,0.10)', // sticky header shadow
              borderTopLeftRadius: 16,
              borderTopRightRadius: 16,
            },
            "& .MuiDataGrid-columnHeader, & .MuiDataGrid-columnHeaderTitle": {
              direction: "rtl",
              textAlign: "right",
              justifyContent: "flex-end",
              paddingRight: "12px !important",
              paddingLeft: "0 !important",
              display: 'flex',
            },
            "& .MuiDataGrid-columnHeaderTitleContainer": {
              flexDirection: "row-reverse",
              direction: 'rtl',
              display: 'flex',
              justifyContent: 'flex-end',
            },
            "& .MuiDataGrid-columnHeaderTitleContainerContent": {
              textAlign: "right",
              justifyContent: "flex-end",
              direction: 'rtl',
              display: 'flex',
            },
            "& .MuiDataGrid-row": {
              minHeight: 44,
              maxHeight: 44,
              transition: 'background 0.2s, box-shadow 0.2s',
              borderRadius: 2,
            },
            "& .MuiDataGrid-row:nth-of-type(even)": { bgcolor: "#f7fafc" }, // lighter stripe
            "& .MuiDataGrid-row:hover": {
              bgcolor: "#e3f2fd",
              boxShadow: '0 2px 8px 0 rgba(30,102,65,0.08)',
              cursor: 'pointer',
            },
            "& .MuiDataGrid-footerContainer": { bgcolor: '#f4f6fa', fontWeight: 'bold', borderBottomLeftRadius: 16, borderBottomRightRadius: 16 },
            "& .MuiDataGrid-virtualScroller": { minHeight: 300 },
            "& .MuiDataGrid-cell": {
              borderBottom: '1px solid #e0e0e0',
              fontWeight: 500,
              fontSize: 17,
              letterSpacing: '0.01em',
            },
            "& .MuiDataGrid-cell:focus, & .MuiDataGrid-columnHeader:focus": {
              outline: 'none',
            },
            "& .MuiDataGrid-root": {
              borderRadius: 4,
            },
          }}
          disableRowSelectionOnClick
          autoHeight
          localeText={{
            noRowsLabel: 'لا توجد بيانات متاحة',
          }}
        />
      </Paper>
      {/* Footer */}
      <Box sx={{ textAlign: 'center', color: '#888', py: 2, fontSize: 16, mt: 'auto' }}>
        © {new Date().getFullYear()} مركز الابتكار
      </Box>
    </Box>
  );
}

export default App;
