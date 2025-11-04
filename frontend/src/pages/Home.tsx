import { Link } from "react-router-dom";
import { Layout } from "../components";

function Home() {
  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-6">
            Welcome to the Educational Assistant
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            Choose a tool to get started
          </p>
          <div className="flex flex-col gap-4 max-w-md mx-auto">
            <Link
              to="/outline-generator"
              className="block px-6 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Course Outline Generator
            </Link>
          </div>
        </div>
      </div>
    </Layout>
  );
}

export default Home;
