import { createContext, ReactNode, useState } from "react";
import LocalPdfViewer from "../components/Popups/LocalPdfViewer";
import LocalImageViewer from "../components/Popups/LocalImageViewer";

interface ImageDetails {
  source: string;
  type: "image" | "pdf";
}

interface GetSet {
  fileDetails: ImageDetails;
  openViewer?: boolean;
  setFileDetails: (imageDetails: ImageDetails) => void;
  setOpenViewer: (state: boolean) => void;
}

export const ImageViewerContext = createContext<GetSet>({
  fileDetails: { source: "", type: "image" },
  openViewer: false,
  setFileDetails: (imageDetails: ImageDetails) => {
    imageDetails;
  },
  setOpenViewer: (state: boolean) => {
    state;
  },
});

const ImageViewerProvider = ({ children }: { children: ReactNode }) => {
  const [openViewer, setOpenViewer] = useState(false);
  const [fileDetails, setFileDetails] = useState<ImageDetails>({
    source: "",
    type: "image",
  });

  return (
    <ImageViewerContext.Provider
      value={{
        fileDetails,
        openViewer,
        setFileDetails,
        setOpenViewer,
      }}
    >
      {fileDetails.type === "image" ? (
        <LocalImageViewer
          open={openViewer}
          imageSource={fileDetails.source}
          setOpen={setOpenViewer}
        />
      ) : (
        <LocalPdfViewer
          url={fileDetails.source}
          open={openViewer}
          setOpen={setOpenViewer}
        />
      )}
      {children}
    </ImageViewerContext.Provider>
  );
};

export default ImageViewerProvider;
