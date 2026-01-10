import { BrowserRouter, Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing";
import OfficerLogin from "./pages/OfficerLogin";
import TemplateForm from "./pages/TemplateForm";
import AccountDetailsProvider from "./contexts/AccountDetailsProvider";
import DashboardPage from "./pages/DashboardPage";
import EventApprovalPage from "./pages/Admin/EventApprovalPage";
import CalendarPage from "./pages/Admin/CalendarPage";
import ReportPage from "./pages/Admin/ReportPage";
import EventProposal from "./pages/Officer/EventProposal";
import FormDataProvider from "./contexts/FormDataProvider";
import RequirementEvalPage from "./pages/Officer/RequirementEvalPage";
import MemebrshipApprovalPage from "./pages/Officer/MemebrshipApprovalPage";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import PublicForm from "./pages/PublicForm";
import ThankYouPage from "./pages/ThankYouPage";
import SnackbarProvider from "./contexts/SnackbarProvider";
import AccountsPage from "./pages/Admin/AccountsPage";
import EventsPage from "./pages/Member/EventsPage";
import ParticipationHistory from "./pages/Member/ParticipationHistory";
import HelpdeskMemberPage from "./pages/Member/HelpdeskMemberPage";
import ImageViewerProvider from "./contexts/ImageViewerProvider";
import QRCode from "./pages/QRCode";
import QrOfficerPage from "./pages/Officer/QrOfficerPage";
import EvaluationDemoPage from "./pages/EvaluationDemoPage";
import AnalyticsPage from "./pages/Admin/AnalyticsPage";
import VolunteerEvaluationPage from "./pages/VolunteerEvaluationPage";
import BeneficiaryEvaluationPage from "./pages/BeneficiaryEvaluationPage";

function App() {
  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <ImageViewerProvider>
        <SnackbarProvider>
          <AccountDetailsProvider>
            <BrowserRouter>
              <FormDataProvider>
                <Routes>
                  <Route path="/">
                    <Route index element={<Landing />} />
                    <Route path="login" element={<OfficerLogin />} />
                    <Route path="template-forms" element={<TemplateForm />} />
                    <Route path="qr" element={<QRCode />} />
                    <Route path="evaluation-demo" element={<EvaluationDemoPage />} />
                    
                    {/* Separate Evaluation Forms */}
                    <Route path="volunteer-evaluation" element={<VolunteerEvaluationPage />} />
                    <Route path="beneficiary-evaluation" element={<BeneficiaryEvaluationPage />} />

                    {/* Evaluation form */}
                    <Route path="evaluation/:id" element={<PublicForm />} />
                    <Route
                      path="feedback-message"
                      element={
                        <ThankYouPage
                          mainMessage="Thank you for your feedback!"
                          subMessage="We truly appreciate your input and will use it to further improve our service"
                        />
                      }
                    />

                    {/* admin route */}
                    <Route path="admin">
                      <Route index element={<DashboardPage />} />
                      <Route path="dashboard" element={<DashboardPage />} />
                      <Route
                        path="event-approval"
                        element={<EventApprovalPage />}
                      />
                      <Route path="calendar" element={<CalendarPage />} />
                      <Route path="report" element={<ReportPage />} />
                      <Route path="accounts" element={<AccountsPage />} />
                      <Route path="analytics" element={<AnalyticsPage />} />
                    </Route>

                    {/* officer route */}
                    <Route path="officer">
                      <Route index element={<DashboardPage />} />
                      <Route path="dashboard" element={<DashboardPage />} />
                      <Route
                        path="event-proposal"
                        element={<EventProposal />}
                      />
                      <Route
                        path="requirement-evaluation"
                        element={<RequirementEvalPage />}
                      />
                      <Route
                        path="membership-approval"
                        element={<MemebrshipApprovalPage />}
                      />
                      <Route
                        path="helpdesk"
                        element={<MemebrshipApprovalPage />}
                      />
                    </Route>

                    {/* members route */}
                    <Route path="member">
                      <Route index element={<EventsPage />} />
                      <Route path="events" element={<EventsPage />} />
                      <Route path="qr-code-share" element={<QrOfficerPage />} />
                      <Route path="helpdesk" element={<HelpdeskMemberPage />} />
                      <Route
                        path="participation"
                        element={<ParticipationHistory />}
                      />
                    </Route>
                  </Route>
                  <Route
                    path="*"
                    element={<ThankYouPage mainMessage="404 | Not Found" />}
                  />
                </Routes>
              </FormDataProvider>
            </BrowserRouter>
          </AccountDetailsProvider>
        </SnackbarProvider>
      </ImageViewerProvider>
    </LocalizationProvider>
  );
}

export default App;
