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
            <div className="mb-6">
              <h2 className="text-2xl font-semibold mb-4 text-gray-800">
                Course Outline Generators
              </h2>
              <div className="flex flex-col gap-3">
                <Link
                  to="/outline-generator"
                  className="block px-6 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-md"
                >
                  📝 Markdown Streaming
                  <span className="block text-sm text-blue-100 mt-1">
                    See content as it's generated, conversational
                  </span>
                </Link>
                <Link
                  to="/structured-outline"
                  className="block px-6 py-4 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium shadow-md"
                >
                  ⚡ Structured Output
                  <span className="block text-sm text-green-100 mt-1">
                    Beautiful cards, validated data, export-ready
                  </span>
                </Link>
              </div>
            </div>

            <div className="border-t border-gray-300 pt-6">
              <Link
                to="/lesson-planner"
                className="block px-6 py-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium shadow-md"
              >
                📚 Lesson Planner
              </Link>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}

export default Home;
