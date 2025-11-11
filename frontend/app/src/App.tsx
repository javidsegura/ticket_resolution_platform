
import { Routes, Route } from "react-router-dom"

import AppLayout from "./layout/app_layout"

import Home from "./pages/Home"
import AboutUs from "./pages/AboutUs"

function App(){
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Home />} />
          <Route path="/AboutUs" element={<AboutUs />} />
      </Route>
      <Route path="*" element={<p>404 error</p>} />
    </Routes>
  )
}


export default App
