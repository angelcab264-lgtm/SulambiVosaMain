import { getImagePath } from "../../utils/imagePath";

const SulambiLogo = () => {
  return (
    <img
      src={getImagePath("/images/logo.png")}
      height="70px"
      width="80px"
      style={{
        borderRadius: "50%",
      }}
    />
  );
};

export default SulambiLogo;
