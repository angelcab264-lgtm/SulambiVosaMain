import FlexBox from "../../components/FlexBox";
import TextHeader from "../../components/Headers/TextHeader";
import TextSubHeader from "../../components/Headers/TextSubHeader";
import PageLayout from "../PageLayout";
import PrimaryButton from "../../components/Buttons/PrimaryButton";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import SelectionCard from "../../components/Cards/SelectionCard";
import { useContext, useEffect, useState } from "react";
import {
  deleteAccount,
  getAllAdminAccounts,
  getAllOfficerAccounts,
  updateAccount,
} from "../../api/accounts";
import { AccountsDataType } from "../../interface/types";
import AccountsForm from "../../components/Forms/AccountsForm";
import { FormDataContext } from "../../contexts/FormDataProvider";
import { SnackbarContext } from "../../contexts/SnackbarProvider";

const AccountsPage: React.FC = () => {
  const { formData, setFormData } = useContext(FormDataContext);
  const { showSnackbarMessage } = useContext(SnackbarContext);

  const [adminAccs, setAdminAccs] = useState([]);
  const [officerAccs, setOfficerAccs] = useState([]);
  const [loading, setLoading] = useState(true);

  const [openAccForm, setOpenAccForm] = useState(false);
  const [editMode, setEditMode] = useState(false);

  const [accountType, setAccountType] = useState("");
  const [forceRefresh, setForceRefresh] = useState(0);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getAllAdminAccounts(),
      getAllOfficerAccounts()
    ]).then(([adminResponse, officerResponse]) => {
      setAdminAccs(adminResponse.data.data ?? []);
      setOfficerAccs(officerResponse.data.data ?? []);
    }).catch((err) => {
      console.error("Error loading accounts:", err);
    }).finally(() => {
      setLoading(false);
    });
  }, [forceRefresh]);

  const createNewAccount = (accountType: "admin" | "officer") => {
    setAccountType(accountType);
    setOpenAccForm(true);
  };

  const updateAccountCallback = () => {
    updateAccount(formData.id, formData)
      .then(() => {
        showSnackbarMessage("Successfully created new account", "success");
      })
      .catch((err) => {
        if (err.response.data) {
          const message = err.response.data.message;
          showSnackbarMessage(`Error Occured: ${message}`, "error");
        } else {
          showSnackbarMessage(
            "An error Occured when registering membership",
            "error"
          );
        }
      })
      .finally(() => {
        setOpenAccForm(false);
        setFormData({});
        setForceRefresh(forceRefresh + 1);
      });
  };

  const deleteAccountCallback = (id: number) => {
    if (id)
      deleteAccount(id)
        .then(() => {
          showSnackbarMessage("Successfully created new account", "success");
        })
        .catch((err) => {
          if (err.response.data) {
            const message = err.response.data.message;
            showSnackbarMessage(`Error Occured: ${message}`, "error");
          } else {
            showSnackbarMessage(
              "An error Occured when registering membership",
              "error"
            );
          }
        })
        .finally(() => {
          setForceRefresh(forceRefresh + 1);
        });
  };

  const commonSx = {
    flex: 1,
    padding: "10px",
    height: "80vh",
    borderRadius: "10px",
    flexDirection: "column",
    backgroundColor: "white",
    boxShadow: "0 0 5px 1px gray",
  };

  const commonBoxSx = {
    width: "100%",
    flexDirection: "column",
    marginTop: "40px",
    textAlign: "center",
    height: "65vh",
    overflowY: "auto",
    gap: "10px",
  };

  return (
    <>
      <AccountsForm
        open={openAccForm}
        setOpen={setOpenAccForm}
        accountType={accountType as "admin" | "officer"}
        onSubmit={() => setForceRefresh(forceRefresh + 1)}
        hideSubmit={editMode}
        componentsBeforeSubmit={
          editMode && (
            <PrimaryButton
              label="Update"
              startIcon={<EditIcon />}
              onClick={updateAccountCallback}
            />
          )
        }
      />
      <PageLayout page="accounts">
        <TextHeader>Accounts</TextHeader>
        <TextSubHeader gutterBottom>
          Add and manage Admin & Officer accounts
        </TextSubHeader>
        {loading ? (
          <FlexBox
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
            minHeight="60vh"
            gap={2}
          >
            <CircularProgress size={60} />
            <Typography variant="h6" color="text.secondary">
              Loading Accounts...
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Please wait while we fetch the account data
            </Typography>
          </FlexBox>
        ) : (
          <FlexBox width="100%" flexDirection="row" gap="20px">
          <FlexBox sx={commonSx}>
            <TextHeader gutterBottom>Admin Accounts</TextHeader>
            <FlexBox>
              <PrimaryButton
                label="Add Admin Account"
                startIcon={<AddIcon />}
                onClick={() => {
                  setFormData({});
                  setEditMode(false);
                  createNewAccount("admin");
                }}
              />
            </FlexBox>
            <FlexBox sx={commonBoxSx}>
              {adminAccs.length === 0 && <TextSubHeader>No Data</TextSubHeader>}
              {adminAccs.map((admin: AccountsDataType, id) => (
                <SelectionCard
                  key={"selection_" + id}
                  header={admin.username}
                  actions={[
                    {
                      label: "Update",
                      icon: <EditIcon />,
                      onClick: () => {
                        setFormData({
                          ...admin,
                          password: undefined,
                        });
                        setEditMode(true);
                        createNewAccount("admin");
                      },
                    },
                    {
                      label: "Delete",
                      icon: <DeleteIcon />,
                      onClick: () => {
                        deleteAccountCallback(admin.id);
                      },
                    },
                  ]}
                />
              ))}
            </FlexBox>
          </FlexBox>

          <FlexBox sx={commonSx}>
            <TextHeader gutterBottom>Officer Accounts</TextHeader>
            <FlexBox>
              <PrimaryButton
                label="Add Officer Account"
                startIcon={<AddIcon />}
                onClick={() => {
                  setFormData({});
                  setEditMode(false);
                  createNewAccount("officer");
                }}
              />
            </FlexBox>
            <FlexBox sx={commonBoxSx}>
              {officerAccs.length === 0 && (
                <TextSubHeader>No Data</TextSubHeader>
              )}
              {officerAccs.map((officer: AccountsDataType, id) => (
                <SelectionCard
                  key={"selection_officer_" + id}
                  header={officer.username}
                  actions={[
                    {
                      label: "Update",
                      icon: <EditIcon />,
                      onClick: () => {
                        setFormData({
                          ...officer,
                          password: undefined,
                        });
                        setEditMode(true);
                        createNewAccount("officer");
                      },
                    },
                    {
                      label: "Delete",
                      icon: <DeleteIcon />,
                      onClick: () => {
                        deleteAccountCallback(officer.id);
                      },
                    },
                  ]}
                />
              ))}
            </FlexBox>
          </FlexBox>
        </FlexBox>
        )}
      </PageLayout>
    </>
  );
};

export default AccountsPage;
