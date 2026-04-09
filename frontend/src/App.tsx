function App() {
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <h1 className="text-4xl font-bold text-blue-600 shadow-md p-4 rounded-xl">
        Tailwind is Working!
      </h1>
      <p className="mt-4 text-gray-500">
        API Bound natively to: {import.meta.env.VITE_API_BASE_URL}
      </p>
    </div>
  )
}

export default App
