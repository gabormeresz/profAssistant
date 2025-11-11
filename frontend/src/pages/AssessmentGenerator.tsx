import { Layout, Header } from "../components";
import { useTranslation } from "react-i18next";

function AssessmentGenerator() {
  const { t } = useTranslation();

  return (
    <Layout
      showSidebar
      header={<Header title={t("header.assessmentGenerator")} />}
    >
      <> </>
    </Layout>
  );
}

export default AssessmentGenerator;
