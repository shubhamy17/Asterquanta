import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { UserList } from "./components/userList";
import { UserDashboard } from "./components/userDashboard";

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<UserList />} />
        <Route path="/:userId" element={<UserDashboard />} />
      </Routes>
    </Router>
  );
};

export default App;
