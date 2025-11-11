import { Layout, Header } from "../components";
import { useTranslation } from "react-i18next";

function PresentationGenerator() {
  const { t } = useTranslation();

  return (
    <Layout
      showSidebar
      header={<Header title={t("header.presentationGenerator")} />}
    >
      <> </>
    </Layout>
  );
}

export default PresentationGenerator;
