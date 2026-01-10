import { createContext, ReactNode, useState, useEffect } from "react";
import { MembershipType } from "../interface/types";
import { getFromStorage, saveToStorage, getStringFromStorage } from "../utils/storage";

interface AccountDetails {
  username: string;
  accountType: "admin" | "officer" | "member";
  details?: MembershipType;
}

interface Pair {
  accountDetails: AccountDetails;
  setAccountDetails: (state: AccountDetails) => void;
}

export const AccountDetailsContext = createContext<Pair>({
  accountDetails: { username: "", accountType: "admin", details: undefined },
  setAccountDetails: (_state: AccountDetails) => {},
});

const AccountDetailsProvider = ({ children }: { children: ReactNode }) => {
  // Initialize account details from localStorage
  const [accountDetails, setAccountDetails] = useState<AccountDetails>(() => {
    const savedUsername = getStringFromStorage("username", "");
    const savedAccountType = getStringFromStorage("accountType", "") as
      | "admin"
      | "member"
      | "officer"
      | "";
    const savedDetails = getFromStorage<MembershipType>("membershipCache", undefined);

    return {
      username: savedUsername || "",
      accountType: savedAccountType || "admin",
      details: savedDetails,
    };
  });

  // Save account details to localStorage whenever it changes
  useEffect(() => {
    if (accountDetails.username) {
      saveToStorage("accountDetails", accountDetails);
    }
  }, [accountDetails]);

  return (
    <AccountDetailsContext.Provider
      value={{ accountDetails, setAccountDetails }}
    >
      {children}
    </AccountDetailsContext.Provider>
  );
};

export default AccountDetailsProvider;
