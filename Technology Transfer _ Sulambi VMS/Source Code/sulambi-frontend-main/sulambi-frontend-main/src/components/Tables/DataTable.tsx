import { Box, IconButton, Typography } from "@mui/material";
import FlexBox from "../FlexBox";
import TextHeaderNormal from "../Headers/TextHeaderNormal";
import CustomInput from "../Inputs/CustomInput";
import SearchIcon from "@mui/icons-material/Search";
import { ReactNode, cloneElement, isValidElement } from "react";

interface DataTableProps {
  title: string;
  fields: string[];
  data: any[][];
  width?: string;
  height?: string;
  componentBeforeSearch?: ReactNode[];
  componentOnLeft?: ReactNode[];
  onSearch?: (key: string) => void;
}

const Table: React.FC<{ children: ReactNode }> = ({ children }) => {
  return (
    <table className="tableData" width="100%">
      {children}
    </table>
  );
};

const DataTable: React.FC<DataTableProps> = ({
  data,
  fields,
  title,
  width,
  height,
  componentBeforeSearch,
  componentOnLeft,
  onSearch,
}) => {
  return (
    <Box
      margin="auto"
      width={width ?? "calc(100% - 40px)"}
      height={height ?? "80vh"}
      padding="20px"
      borderRadius="10px"
      boxShadow="0 0 10px 1px gray"
      marginTop="40px"
    >
      {/* Table title */}
      <TextHeaderNormal gutterBottom>{title}</TextHeaderNormal>
      <Box display="grid" width="100%" gridTemplateColumns="auto auto">
        <FlexBox
          width="calc(100% - 20px)"
          justifyContent="flex-start"
          gap="20px"
        >
          {componentOnLeft?.map((component, index) => 
            isValidElement(component) 
              ? cloneElement(component, { key: index })
              : <span key={index}>{component}</span>
          )}
        </FlexBox>
        <FlexBox width="calc(100% - 20px)" justifyContent="flex-end" gap="20px">
          {componentBeforeSearch?.map((component, index) => 
            isValidElement(component) 
              ? cloneElement(component, { key: index })
              : <span key={index}>{component}</span>
          )}
          <CustomInput
            placeholder="Search by name, email, SR code, event, department..."
            onChange={(event) => onSearch && onSearch(event.target.value)}
            endIcon={
              <IconButton>
                <SearchIcon />
              </IconButton>
            }
            forceEnd={true}
            sx={{
              minWidth: "300px"
            }}
          />
        </FlexBox>
      </Box>

      {/* table header container */}
      <Box marginTop="30px" paddingLeft="10px" paddingRight="10px">
        <Table>
          <thead>
            <tr>
              {fields.map((field, index) => (
                <th key={index}>{field}</th>
              ))}
            </tr>
          </thead>
        </Table>
      </Box>

      {/* table container */}
      <Box
        width="calc(100% - 10px)"
        maxHeight="60vh"
        overflow="auto"
        paddingLeft="10px"
        paddingRight="10px"
        sx={{
          scrollbarWidth: "thin",
        }}
      >
        {data.length > 0 ? (
          <Table>
            <tbody>
              {data.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {row.map((coldata, colIndex) => (
                    <td key={colIndex}>{coldata}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </Table>
        ) : (
          <FlexBox
            width="100%"
            justifyContent="center"
            alignItems="center"
            paddingTop="20px"
          >
            <Typography>No data available</Typography>
          </FlexBox>
        )}
      </Box>
    </Box>
  );
};

export default DataTable;
