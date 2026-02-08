import { useTranslation } from "react-i18next";
import { Layout, Header } from "../components";

function AppPage() {
  const { t } = useTranslation();

  return (
    <Layout showSidebar header={<Header title={t("app.title")} />}>
      <></>
    </Layout>
  );
}

export default AppPage;
