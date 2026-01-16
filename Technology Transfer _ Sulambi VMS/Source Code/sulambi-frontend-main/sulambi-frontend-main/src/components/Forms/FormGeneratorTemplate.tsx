import { ReactNode, useContext, useEffect, useState, useRef, useMemo } from "react";
import FlexBox from "../FlexBox";
import FlexRowBox from "../FlexRowBox";
import CustomInput from "../Inputs/CustomInput";
import CustomDropdown from "../Inputs/CustomDropdown";
import CustomDivider from "../Divider/CustomDivider";
import { TextareaAutosize, Typography, IconButton, Box } from "@mui/material";
import CustomCheckbox from "../Inputs/CustomCheckbox";
import { CheckBoxDataType, RadioListDataType } from "../../interface/types";
import PrimaryButton from "../Buttons/PrimaryButton";
import { FormDataContext } from "../../contexts/FormDataProvider";
import { DateTimePicker } from "@mui/x-date-pickers";
import CustomRadiolist from "../Inputs/CustomRadiolist";
import dayjs from "dayjs";
// import DownloadIcon from "@mui/icons-material/Download";
import RemoveRedEyeIcon from "@mui/icons-material/RemoveRedEye";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import { ImageViewerContext } from "../../contexts/ImageViewerProvider";
import RichTextEditor from "../Inputs/RichTextEditor";
import SafeHtmlRenderer from "../Inputs/SafeHtmlRenderer";
import EditableGanttTable from "../Tables/EditableGanttTable";

const BASE_API_URL = import.meta.env.VITE_API_URI ?? "http://localhost:8000/api";

export interface FormGenTemplateProps {
  id?: string;
  /**
   * Internal flag used by FieldRepeater so FormGeneratorTemplate won't bind
   * the input to top-level formData[value.id]. FieldRepeater manages its own
   * nested state under formData[fieldKey].
   */
  fromFieldRepeater?: boolean;
  type:
    | "dropdown"
    | "text"
    | "password"
    | "file"
    | "textQuestion"
    | "number"
    | "section"
    | "checkbox"
    | "radiolist"
    | "divider"
    | "label"
    | "dynamicMultiType"
    | "break"
    | "component"
    | "fieldRepeater"
    | "datetime"
    | "ganttTable";
  message?: string;
  icon?: ReactNode;
  endIcon?: ReactNode;
  field?: (FormGenTemplateProps | FormGenTemplateProps[])[];
  fieldKey?: string;
  flex?: number;
  hidden?: boolean;
  value?: any;
  error?: boolean;
  required?: boolean;
  setValue?: (value: any) => void;
  onUse?: (event: any) => void;
  hideOnView?: boolean;
  showOnView?: boolean;
  selectionQuestion?: CheckBoxDataType[];
  component?: ReactNode;
  placeholder?: string;
  disabled?: boolean;
  radioListRowDirection?: boolean;
  menu?: {
    key: string;
    value: any;
  }[];
  initialColumns?: string[];
  initialData?: { [rowIndex: string]: { [colKey: string]: string } };
}

interface TitleTextProps {
  text: string;
}

interface TextAreaQuestionProps {
  question: string;
  required?: boolean;
  value?: string;
  error?: boolean;
  placeholder?: string;
  disabled?: boolean;
  onChange?: (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
}

interface FileInputProps extends TextAreaQuestionProps {
  flex?: number;
  isMultiUpload?: boolean;
}

interface CheckBoxQuestionProps {
  question: string;
  selectionQuestion: CheckBoxDataType[];
  flex?: number;
  values?: any[];
  required?: boolean;
  onChange?: (value: any) => void;
}

interface RadioListQuestionProps {
  question: string;
  flex?: number;
  value?: any;
  viewOnly?: boolean;
  selectionQuestion: RadioListDataType[];
  rowDirection?: boolean;
  required?: boolean;
  onChange?: (value: any) => void;
}

interface FieldRepeaterProps {
  field: (FormGenTemplateProps | FormGenTemplateProps[])[];
  label?: string;
  fieldKey: string;
}

interface ViewOnlyFieldProps {
  question: string;
  value: string;
  flex?: number;
}

interface Props {
  template: (FormGenTemplateProps | FormGenTemplateProps[])[];
  fieldErrors: string[];
  forceRefresh?: number;
  enableAutoFieldCheck?: boolean;
  dataLoader?: boolean;
  viewOnly?: boolean;
}

const InputQuestionWrapper = ({
  children,
  message,
  required,
  flex,
}: {
  message?: string;
  required?: boolean;
  children?: ReactNode;
  flex?: number;
}) => {
  return (
    <FlexBox flexDirection="column" flex={flex ?? 1} width="100%">
      <Typography color="var(--text-landing)">
        {message}
        {required && <b style={{ color: "red" }}>*</b>}
      </Typography>
      {children}
    </FlexBox>
  );
};

const FieldRepeater = ({ field, fieldKey }: FieldRepeaterProps) => {
  const [added, setAdded] = useState(0);
  const [localValues, setLocalValues] = useState<any>({});
  const { immutableSetFormData, formData } = useContext(FormDataContext);
  const lastInitializedRef = useRef<string>("");
  const fieldKeyRef = useRef<string>(fieldKey);
  const isUpdatingFromFormDataRef = useRef<boolean>(false);

  const [localFields, setLocalFields] = useState<
    (FormGenTemplateProps | FormGenTemplateProps[])[][]
  >([]);

  // Reset initialization when fieldKey changes
  useEffect(() => {
    if (fieldKeyRef.current !== fieldKey) {
      fieldKeyRef.current = fieldKey;
      lastInitializedRef.current = "";
      setLocalValues({});
      setAdded(0);
    }
  }, [fieldKey]);

  // Initialize from formData if it exists and hasn't been initialized yet
  useEffect(() => {
    // Skip if we're in the middle of updating from formData to prevent loops
    if (isUpdatingFromFormDataRef.current) return;

    if (formData && formData[fieldKey]) {
      const existingData = formData[fieldKey];
      // Check if existingData is a valid object with entries
      if (existingData && typeof existingData === 'object' && Object.keys(existingData).length > 0) {
        const existingDataStr = JSON.stringify(existingData);
        
        // Only initialize if this data hasn't been initialized yet
        if (lastInitializedRef.current !== existingDataStr) {
          // Count the number of rows (assuming numeric keys like 0, 1, 2, etc.)
          const numericKeys = Object.keys(existingData).map(key => parseInt(key)).filter(key => !isNaN(key));
          const rowCount = numericKeys.length > 0 ? Math.max(...numericKeys) + 1 : Object.keys(existingData).length;
          
          // Only update if we have a meaningful change
          if (rowCount > 0) {
            isUpdatingFromFormDataRef.current = true;
            setLocalValues(existingData);
            setAdded(rowCount);
            lastInitializedRef.current = existingDataStr;
            // Reset the flag after state updates
            setTimeout(() => {
              isUpdatingFromFormDataRef.current = false;
            }, 0);
          }
        }
      } else if (!existingData || Object.keys(existingData).length === 0) {
        // Reset if formData for this field is empty
        if (lastInitializedRef.current !== "") {
          setLocalValues({});
          setAdded(0);
          lastInitializedRef.current = "";
        }
      }
    } else if (!formData || !formData[fieldKey]) {
      // Reset if formData no longer has this field
      if (lastInitializedRef.current !== "" && added > 0) {
        setLocalValues({});
        setAdded(0);
        lastInitializedRef.current = "";
      }
    }
  }, [formData?.[fieldKey], fieldKey]);

  // Update formData only when localValues change (but not during initialization)
  useEffect(() => {
    // Don't update formData during initialization from formData
    if (isUpdatingFromFormDataRef.current) return;
    
    // Only update if we have actual data or if we're clearing
    if (Object.keys(localValues).length > 0 || lastInitializedRef.current !== "") {
      immutableSetFormData({ [fieldKey]: localValues });
    }
  }, [localValues, fieldKey]);

  const onUseCallback = (event: any, index: number, fieldId: string) => {
    setLocalValues((prev: any) => ({
      ...prev,
      [index]: {
        ...prev[index],
        [fieldId]: event.target.value,
      },
    }));
  };

  const fieldCallbackParser = (
    fieldValues: (FormGenTemplateProps | FormGenTemplateProps[])[],
    index: number
  ): (FormGenTemplateProps | FormGenTemplateProps[])[] => {
    return fieldValues.map((indivField) => {
      if (Array.isArray(indivField))
        return fieldCallbackParser(indivField, index) as FormGenTemplateProps[];
      // Get the initial value from localValues if it exists
      const initialValue = localValues[index]?.[indivField.id ?? "_"] ?? "";
      return {
        ...indivField,
        fromFieldRepeater: true,
        value: initialValue,
        onUse: (event: any) => {
          onUseCallback(event, index, indivField.id ?? "_");
          // mutableSetFormData({
          //   [fieldKey]: {
          //     ...formData[fieldKey],
          //     [indivField.id ?? "_"]: event.target.value,
          //   },
          // });
        },
      };
    });
  };

  // Update fields when added or localValues change, using useMemo to prevent unnecessary recalculations
  const localFieldsMemo = useMemo(() => {
    const repeatedFields: (FormGenTemplateProps | FormGenTemplateProps[])[][] =
      [];

    for (let i = 0; i < added; i++) {
      repeatedFields.push(fieldCallbackParser(field, i));
    }

    return repeatedFields;
  }, [added, localValues, field]);

  useEffect(() => {
    setLocalFields(localFieldsMemo);
  }, [localFieldsMemo]);

  return (
    <>
      {localFields.length > 0 &&
        localFields.map((fld, idx) => (
          <FormGeneratorTemplate
            key={`${fieldKeyRef.current}-${idx}`}
            fieldErrors={[]}
            template={[
              ...fld,
              {
                type: "divider",
              },
            ]}
          />
        ))}
      <FlexRowBox width="100%">
        <PrimaryButton
          fullWidth
          label="Add Field"
          sx={{ flex: 1 }}
          onClick={() => {
            setAdded(added + 1);
          }}
        />
      </FlexRowBox>
    </>
  );
};

const TextAreaQuestion = ({
  error,
  disabled,
  question,
  onChange,
  required,
  placeholder,
  value,
}: TextAreaQuestionProps) => {
  // Use RichTextEditor for all textQuestion fields (Event Proposal Form fields)
  return (
    <RichTextEditor
      question={question}
      required={required}
      value={value || ''}
      onChange={(newValue) => {
        // Convert ReactQuill onChange to match TextAreaQuestion onChange signature
        if (onChange) {
          const event = {
            target: { value: newValue }
          } as React.ChangeEvent<HTMLTextAreaElement>;
          onChange(event);
        }
      }}
      error={error}
      placeholder={placeholder}
      disabled={disabled}
    />
  );
};

const ViewOnlyField = ({ question, value, flex }: ViewOnlyFieldProps) => {
  // Check if the value contains HTML tags
  const hasHtmlTags = value && typeof value === 'string' && /<[^>]*>/g.test(value);
  
  return (
    <FlexBox flexDirection="column" flex={flex ?? 1} width="100%">
      <Typography color="var(--text-landing)">{question}</Typography>
      {hasHtmlTags ? (
        <SafeHtmlRenderer 
          htmlContent={value || ''} 
          style={{ 
            border: '1px solid #ccc', 
            padding: '8px', 
            borderRadius: '4px',
            minHeight: '40px',
            backgroundColor: '#f9f9f9'
          }} 
        />
      ) : (
        <CustomInput value={value} width="100%" disabled />
      )}
    </FlexBox>
  );
};

const FileInput = ({
  question,
  onChange,
  value,
  required,
  flex,
  error,
  isMultiUpload,
}: FileInputProps) => {
  return (
    <FlexBox flexDirection="column" flex={flex}>
      <Typography color="var(--text-landing)">
        {question}
        {required && <b style={{ color: "red" }}>*</b>}
      </Typography>
      <CustomInput
        isMultiUpload={isMultiUpload}
        value={value}
        onChange={onChange}
        type="file"
        error={error}
      />
    </FlexBox>
  );
};

const TitleText = ({ text }: TitleTextProps) => {
  return (
    <FlexBox width="100%">
      <Typography fontWeight="bold" color="var(--text-landing)">
        {text}
      </Typography>
    </FlexBox>
  );
};

const CheckBoxQuestion = ({
  flex,
  values,
  question,
  selectionQuestion,
  required,
  onChange,
}: CheckBoxQuestionProps) => {
  return (
    <FlexBox
      flex={flex}
      padding="10px"
      border="1px solid #bdbdbd"
      borderRadius="5px"
      flexDirection="column"
      width="100%"
    >
      <Typography color="var(--text-landing)">
        {question}
        {required && <b style={{ color: "red" }}>*</b>}
      </Typography>
      <CustomCheckbox
        values={values}
        checkboxData={selectionQuestion}
        onChange={onChange}
      />
    </FlexBox>
  );
};

const RadioListQuestion = ({
  question,
  rowDirection,
  selectionQuestion,
  flex,
  value,
  viewOnly,
  required,
  onChange,
}: RadioListQuestionProps) => {
  return (
    <FlexBox
      flex={flex}
      padding="10px"
      border="1px solid #bdbdbd"
      borderRadius="5px"
      flexDirection="column"
      width="100%"
    >
      <Typography
        color="var(--text-landing)"
        // textAlign={rowDirection ? "center" : "inherit"}
      >
        {question}
        {required && <b style={{ color: "red" }}>*</b>}
      </Typography>
      <CustomRadiolist
        viewOnly={viewOnly}
        value={value}
        onChange={onChange}
        rowDirection={rowDirection}
        radioListData={selectionQuestion}
      />
    </FlexBox>
  );
};

const FormGeneratorTemplate = ({
  fieldErrors,
  template,
  forceRefresh,
  enableAutoFieldCheck,
  viewOnly,
}: Props) => {
  const [templateState, setTemplateState] = useState(template);
  const { formData, immutableSetFormData } = useContext(FormDataContext);
  const { setFileDetails, setOpenViewer } = useContext(ImageViewerContext);

  useEffect(() => {
    setTemplateState(template);
  }, [forceRefresh, viewOnly]);

  return template.length > 0 ? (
    <>
      {templateState.length > 0 ? (
        template.map((value, index) => {
          if (Array.isArray(value)) {
            return (
              <FlexRowBox key={index} width="100%">
                <FormGeneratorTemplate
                  viewOnly={viewOnly}
                  enableAutoFieldCheck={enableAutoFieldCheck}
                  template={value}
                  fieldErrors={fieldErrors}
                />
              </FlexRowBox>
            );
          }

          if (viewOnly && value.hideOnView === true) return null;
          if (viewOnly && value.showOnView === false) return null;
          if (!viewOnly && value.hidden) return null;
          if (
            viewOnly &&
            ![
              "label",
              "textQuestion",
              "file",
              "divider",
              "radiolist",
              "fieldRepeater",
              "dynamicMultiType",
              "checkbox",
              "section",
              "break",
            ].includes(value.type)
          )
            return (
              <ViewOnlyField
                flex={value.flex}
                question={value.message ?? ""}
                value={formData[value.id ?? ""] ?? value.value}
              />
            );

          if (viewOnly && value.type === "file")
            return (
              <FlexBox
                flexDirection="column"
                flex={value.flex ?? 1}
                width="100%"
              >
                <Typography>{value.message}</Typography>
                {value.id && formData[value.id] && String(formData[value.id]).trim() !== "" && String(formData[value.id]) !== "N/A" ? (
                  <PrimaryButton
                    label="View Uploaded File"
                    startIcon={<RemoveRedEyeIcon />}
                    onClick={() => {
                      const raw = String(formData[value.id]);
                      
                      // Check if it's a Cloudinary URL or other full URL
                      const isFullUrl = raw.startsWith("http://") || raw.startsWith("https://");
                      
                      let fileSource: string;
                      let isPdf: boolean;
                      
                      if (isFullUrl) {
                        // Use Cloudinary URL or other full URL directly
                        fileSource = raw;
                        // Check if URL ends with .pdf or contains pdf in path/query
                        const lower = raw.toLowerCase();
                        // More robust PDF detection: check extension, content-type hints, or Cloudinary format
                        isPdf = 
                          lower.endsWith(".pdf") || 
                          lower.includes(".pdf?") ||
                          lower.includes("/pdf/") ||
                          lower.includes("format=pdf") ||
                          lower.includes("fl_pdf") ||
                          (lower.includes("pdf") && !lower.match(/\.(jpg|jpeg|png|gif|webp|svg)/));
                      } else {
                        // Handle local uploads
                        const base = (BASE_API_URL as string).replace("/api", "");
                        const rootUri = `${base}/uploads`;

                        // Backend may store paths like "uploads/<file>" or "uploads\\<file>".
                        // Normalize into a URL path relative to /uploads/<path>
                        const normalized = raw.replace(/\\/g, "/");
                        const relative = normalized.startsWith("uploads/")
                          ? normalized.slice("uploads/".length)
                          : normalized;

                        fileSource = `${rootUri}/${relative}`;
                        const lower = relative.toLowerCase();
                        isPdf = lower.endsWith(".pdf");
                      }
                      
                      console.log("[PDF_VIEWER] File detection:", {
                        raw,
                        fileSource,
                        isPdf,
                        isFullUrl
                      });

                      setFileDetails({
                        source: fileSource,
                        type: isPdf ? "pdf" : "image",
                      });
                      setOpenViewer(true);
                    }}
                  />
                ) : (
                  <Typography color="text.secondary" sx={{ fontStyle: "italic", padding: "8px" }}>
                    No file uploaded
                  </Typography>
                )}
              </FlexBox>
            );

          if (value.type === "break") return <br key={`break-${index}`} />;

          // text input type
          if (value.type === "text") {
            // Compute the current value - use formData[id] if id exists, otherwise use value.value
            // But value.value might be a function or computed value, so we need to handle it
            let currentValue = value.fromFieldRepeater
              ? value.value
              : (value.id ? formData[value.id] : value.value);
            
            // If value.value is undefined or null, and we have an onUse callback that reads from formData,
            // we should compute it from the callback context (but we can't do that here)
            // So we rely on the value prop being reactive, which it should be since ExternalForm is recreated on each render
            
            return (
              <InputQuestionWrapper
                key={`text-${index}`}
                message={value.message}
                flex={value.flex}
                required={value.required}
              >
                <CustomInput
                  key={index}
                  disabled={viewOnly ?? value.disabled}
                  autoComplete={value.id === "username" ? "off" : undefined}
                  name={value.id === "username" ? "new-username" : value.id}
                  // flex={value.flex ?? 1}
                  // placeholder={value.message}
                  startIcon={value.icon}
                  endIcon={value.endIcon}
                  value={currentValue ?? ""}
                  error={value.id ? fieldErrors.includes(value.id) : false}
                  onChange={(event: any) => {
                    // For FieldRepeater children, the repeater manages nested formData updates.
                    if (enableAutoFieldCheck && value.id && !value.fromFieldRepeater) {
                      immutableSetFormData({ [value.id]: event.target.value });
                      return value.onUse && value.onUse(event);
                    }

                    value.onUse && value.onUse(event);
                  }}
                />
              </InputQuestionWrapper>
            );
          }

          if (value.type === "password") {
            const [showPassword, setShowPassword] = useState(false);
            const passwordValue = formData[value.id ?? ""] ?? value.value ?? "";
            
            // Password validation
            const hasMinLength = passwordValue?.length >= 8;
            const hasUppercase = /[A-Z]/.test(passwordValue);
            const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(passwordValue);
            const isPasswordValid = hasMinLength && hasUppercase && hasSpecialChar;
            
            return (
              <InputQuestionWrapper
                key={`password-${index}`}
                message={value.message}
                flex={value.flex}
                required={value.required}
              >
                <CustomInput
                  key={index}
                  disabled={viewOnly ?? value.disabled}
                  type={showPassword ? "text" : "password"}
                  autoComplete={"new-password"}
                  name={"new-password"}
                  startIcon={value.icon}
                  endIcon={
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                      size="small"
                      sx={{
                        '&:hover': {
                          bgcolor: 'action.hover'
                        }
                      }}
                    >
                      {showPassword ? <VisibilityOffIcon /> : <RemoveRedEyeIcon />}
                    </IconButton>
                  }
                  forceEnd={true}
                  value={passwordValue}
                  error={value.id ? fieldErrors.includes(value.id) : false}
                  helperText={
                    passwordValue
                      ? (
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="caption" color="text.secondary">
                              Password strength:
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 0.5 }}>
                              {[1, 2, 3].map((level) => (
                                <Box
                                  key={level}
                                  sx={{
                                    width: 20,
                                    height: 4,
                                    borderRadius: 2,
                                    bgcolor:
                                      level === 1 && hasMinLength ? '#ff9800' :
                                      level === 2 && hasMinLength && hasUppercase ? '#ff9800' :
                                      level === 3 && isPasswordValid ? '#4caf50' : '#e0e0e0',
                                  }}
                                />
                              ))}
                            </Box>
                            <Typography 
                              variant="caption" 
                              color={
                                isPasswordValid ? 'success.main' :
                                passwordValue.length >= 6 ? 'warning.main' : 'text.secondary'
                              }
                              sx={{ fontWeight: 500 }}
                            >
                              {isPasswordValid ? 'Strong' : passwordValue.length >= 6 ? 'Medium' : 'Weak'}
                            </Typography>
                          </Box>
                        )
                      : null
                  }
                  FormHelperTextProps={{ sx: { mt: 0.5, lineHeight: 1 } }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      '&.Mui-focused': {
                        '& .MuiOutlinedInput-notchedOutline': {
                          borderColor: isPasswordValid ? 'success.main' : 'primary.main',
                        }
                      }
                    }
                  }}
                  onChange={(event: any) => {
                    if (enableAutoFieldCheck && value.id) {
                      immutableSetFormData({ [value.id]: event.target.value });
                      value.onUse && value.onUse(event);
                      return;
                    }

                    value.onUse && value.onUse(event);
                  }}
                />
              </InputQuestionWrapper>
            );
          }

          if (value.type === "file")
            return (
              <FileInput
                key={index}
                question={value.message ?? ""}
                flex={value.flex ?? 1}
                required={value.required}
                error={value.id ? fieldErrors.includes(value.id) : false}
                isMultiUpload={value.id === "photos"}
                onChange={(event: any) => {
                  if (enableAutoFieldCheck && value.id) {
                    if (value.id === "photos")
                      immutableSetFormData({
                        [value.id]: event.target.files,
                      });
                    else
                      immutableSetFormData({
                        [value.id]: event.target.files[0],
                      });
                    value.onUse && value.onUse(event);
                    return;
                  }

                  value.onUse && value.onUse(event);
                }}
              />
            );

          // number input type
          if (value.type === "number")
            return (
              <InputQuestionWrapper
                key={`number-${index}`}
                message={value.message}
                flex={value.flex}
                required={value.required}
              >
                <CustomInput
                  // flex={value.flex ?? 1}
                  // placeholder={value.message}
                  startIcon={value.icon}
                  endIcon={value.endIcon}
                  disabled={viewOnly ?? value.disabled}
                  type="number"
                  value={
                    value.fromFieldRepeater
                      ? (value.value ?? "")
                      : (formData[value.id ?? ""] ?? value.value ?? "")
                  }
                  error={value.id ? fieldErrors.includes(value.id) : false}
                  onChange={(event: any) => {
                    if (enableAutoFieldCheck && value.id && !value.fromFieldRepeater) {
                      immutableSetFormData({ [value.id]: event.target.value });
                      value.onUse && value.onUse(event);
                      return;
                    }

                    value.onUse && value.onUse(event);
                  }}
                />
              </InputQuestionWrapper>
            );

          // dropdown input type
          if (value.type === "dropdown") {
            return (
              <InputQuestionWrapper
                key={`dropdown-${index}`}
                message={value.message}
                flex={value.flex}
                required={value.required}
              >
                <CustomDropdown
                  disabled={viewOnly ?? value.disabled}
                  // label={value.message}
                  // flex={value.flex ?? 1}
                  menu={value.menu ?? []}
                  initialValue={formData[value.id ?? ""] ?? value.value}
                  error={value.id ? fieldErrors.includes(value.id) : false}
                  onChange={(event: any) => {
                    if (enableAutoFieldCheck && value.id) {
                      immutableSetFormData({ [value.id]: event.target.value });
                      value.onUse && value.onUse(event);
                      return;
                    }

                    value.onUse && value.onUse(event);
                  }}
                />
              </InputQuestionWrapper>
            );
          }

          // checkbox input type
          if (value.type === "checkbox")
            return (
              <CheckBoxQuestion
                key={index}
                flex={value.flex ?? 1}
                question={value.message ?? ""}
                selectionQuestion={value.selectionQuestion ?? []}
                required={value.required}
                values={
                  value.id
                    ? (formData[value.id] as any[]) ?? []
                    : (value.value as any[])
                }
                onChange={(data: any) => {
                  if (enableAutoFieldCheck && value.id) {
                    if (!formData[value.id]) {
                      immutableSetFormData({
                        [value.id]: [data],
                      });
                    }

                    // list does not include (add the data)
                    else if (!(formData[value.id] as any[]).includes(data)) {
                      immutableSetFormData({
                        [value.id]: [...formData[value.id], data],
                      });
                    }

                    // list does include: (remove the data)
                    else if ((formData[value.id] as any[]).includes(data)) {
                      immutableSetFormData({
                        [value.id]: (formData[value.id] as any[]).filter(
                          (d) => d !== data
                        ),
                      });
                    }

                    value.onUse && value.onUse(data);
                    return;
                  }

                  value.onUse && value.onUse(data);
                }}
              />
            );

          // checkbox input type
          if (value.type === "radiolist")
            return (
              <RadioListQuestion
                key={index}
                viewOnly={viewOnly}
                required={value.required}
                question={value.message ?? ""}
                selectionQuestion={value.selectionQuestion ?? []}
                rowDirection={value.radioListRowDirection}
                flex={value.flex ?? 1}
                value={value.id ? formData[value.id] ?? "" : value.value ?? ""}
                onChange={(selectedRadio) => {
                  if (enableAutoFieldCheck && value.id) {
                    immutableSetFormData({ [value.id]: selectedRadio });
                    value.onUse && value.onUse(event);
                    return;
                  }

                  value.onUse && value.onUse(selectedRadio);
                }}
              />
            );

          // section with title
          if (value.type === "section")
            return (
              <div key={`section-${index}`}>
                <CustomDivider width="100%" />
                <TitleText text={value.message ?? ""} />
              </div>
            );

          if (value.type === "textQuestion")
            return (
              <TextAreaQuestion
                key={`textQuestion-${index}`}
                question={value.message ?? ""}
                required={value.required}
                value={formData[value.id ?? ""] ?? value.value}
                error={value.id ? fieldErrors.includes(value.id) : false}
                placeholder={value.placeholder}
                disabled={viewOnly ?? value.disabled}
                onChange={(event: any) => {
                  if (enableAutoFieldCheck && value.id) {
                    immutableSetFormData({ [value.id]: event.target.value });
                    value.onUse && value.onUse(event);
                    return;
                  }

                  value.onUse && value.onUse(event);
                }}
              />
            );

          if (value.type === "datetime")
            return (
              <InputQuestionWrapper
                key={`datetime-${index}`}
                message={value.message}
                flex={value.flex}
                required={value.required}
              >
                <DateTimePicker
                  value={
                    value.id
                      ? dayjs(formData[value.id]).isValid()
                        ? formData[value.id]
                          ? dayjs(formData[value.id])
                          : undefined
                        : value.value ?? undefined
                      : undefined
                  }
                  slotProps={{
                    textField: {
                      // placeholder: value.message,
                      fullWidth: true,
                      size: "small",
                      sx: {
                        borderRadius: "10px",
                        border:
                          value.id && fieldErrors.includes(value.id)
                            ? "1px solid red"
                            : "",
                      },
                    },
                  }}
                  // sx={{ flex: value.flex }}
                  onChange={(val) => {
                    if (val && enableAutoFieldCheck && value.id) {
                      immutableSetFormData({
                        [value.id]: val.toDate().getTime(),
                      });
                      value.onUse && value.onUse(event);
                      return;
                    }
                    value.onUse && value.onUse(val);
                  }}
                />
              </InputQuestionWrapper>
            );

          if (value.type === "label")
            return (
              <Typography key={`label-${index}`} color="var(--text-landing)" variant="body1">
                {value.message}
              </Typography>
            );

          if (value.type === "fieldRepeater" && value.fieldKey)
            return (
              <FieldRepeater
                key={`fieldRepeater-${index}`}
                field={value.field ?? []}
                fieldKey={value.fieldKey}
              />
            );

          if (value.type === "ganttTable" && value.fieldKey)
            return (
              <Box key={`ganttTable-${index}`} sx={{ width: '100%', marginBottom: '20px' }}>
                {value.message && (
                  <Typography variant="h6" sx={{ marginBottom: '10px', fontWeight: 'bold' }}>
                    {value.message}
                  </Typography>
                )}
                <EditableGanttTable
                  key={`gantt-${value.fieldKey}-${viewOnly}`}
                  fieldKey={value.fieldKey}
                  initialData={value.initialData || (formData[value.fieldKey] && Object.keys(formData[value.fieldKey]).length > 0 ? formData[value.fieldKey] : {})}
                  initialColumns={value.initialColumns || ['Activities', 'Month 1', 'Month 2', 'Month 3', 'Month 4', 'Month 5', 'Month 6']}
                  viewOnly={viewOnly}
                />
              </Box>
            );

          if (value.type === "divider") return <CustomDivider key={`divider-${index}`} width="100%" />;
          if (value.type === "component") {
            return (
              <Box 
                key={`component-${index}`} 
                sx={{ 
                  flex: value.flex ?? 1, 
                  width: value.flex ? 'auto' : '100%',
                  display: 'flex'
                }}
              >
                {value.component}
              </Box>
            );
          }
        })
      ) : (
        <></>
      )}
    </>
  ) : (
    <></>
  );
};

export default FormGeneratorTemplate;
