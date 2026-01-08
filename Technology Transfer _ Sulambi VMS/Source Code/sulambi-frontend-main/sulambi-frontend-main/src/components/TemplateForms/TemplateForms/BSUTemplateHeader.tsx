import { BsuTemplateHeaderProps } from "../../../interface/props";
import FlexBox from "../../FlexBox";
import { getImagePath } from "../../../utils/imagePath";

const BSUTemplateHeader: React.FC<BsuTemplateHeaderProps> = ({
  children,
  effectivityDate,
  formTitle,
  reference,
  revisionNumber,
  romaize,
}) => {
  return (
    <FlexBox 
      width="100%" 
      alignItems="center" 
      flexDirection="column"
      className="bsu-form-wrapper"
      sx={{ 
        pageBreakInside: "auto", 
        breakInside: "auto",
        gap: 0,
        rowGap: 0,
        "& > table.bsuForm": {
          marginBottom: 0,
        },
        "& > table.bsuForm + table.bsuFormChild": {
          marginTop: "0 !important",
          borderTop: "none !important",
        },
        "& > table.bsuForm ~ table.bsuFormChild": {
          marginTop: "0 !important",
          borderTop: "none !important",
        },
        "@media print": {
          "& > table.bsuForm:first-child": {
            pageBreakAfter: "auto !important",
            breakAfter: "auto !important",
            marginBottom: "5px !important",
          },
          "& > table.bsuForm:first-child + table.bsuFormChild": {
            pageBreakBefore: "auto !important",
            breakBefore: "auto !important",
            marginTop: "0 !important",
          },
        },
      }}
    >
      <div className="header-content-group" style={{ width: "100%" }}>
        <table className="bsuForm" style={{ marginBottom: 0, marginTop: 0 }}>
          <tbody>
            <tr>
              <td
                width="10%"
                style={{ textAlign: "center" }}
                className={romaize ? "fontSet" : ""}
              >
                <img src={getImagePath("/images/bsu-logo.png")} height="50px" width="55px" style={{ margin: 0, padding: 0 }} />
              </td>
              <td width="35%" className={romaize ? "fontSet" : ""}>
                {reference ?? "Reference No.: BatStateU-REC-ESO-02"}
              </td>
              <td width="35%" className={romaize ? "fontSet" : ""}>
                {effectivityDate ?? "Effectivity Date: May 18, 2022"}
              </td>
              <td width="20%" className={romaize ? "fontSet" : ""}>
                {revisionNumber ?? "Revision No.: 02"}
              </td>
            </tr>
            {formTitle ? (
              <tr>
                <td
                  colSpan={4}
                  className={`hasSmallPadding ${romaize ? "fontSet" : ""}`}
                  style={{
                    fontWeight: "bold",
                    fontSize: "10pt",
                    textAlign: "center",
                    padding: "8px 5px",
                    borderTop: "none",
                    borderBottom: "1px solid black",
                  }}
                >
                  {formTitle}
                </td>
              </tr>
            ) : (
              <></>
            )}

          </tbody>
        </table>

        {children}
      </div>
    </FlexBox>
  );
};

export default BSUTemplateHeader;
