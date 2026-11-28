import { NavLink, Navigate, Route, Routes } from 'react-router'
import CalendarPage from './pages/CalendarPage'
import CustomersPage from './pages/CustomersPage'
import NewOrderPage from './pages/NewOrderPage'
import OrdersPage from './pages/OrdersPage'
import ProductsPage from './pages/ProductsPage'
import StandingOrdersPage from './pages/StandingOrdersPage'

export default function App() {
  return (
    <div className="shell">
      <header className="topbar">
        <NavLink to="/orders" className="brand">
          <img src="/favicon.svg" alt="" width={28} height={28} />
          BakeMagic
        </NavLink>
        <nav className="nav">
          <NavLink to="/orders">Orders</NavLink>
          <NavLink to="/standing-orders">Standing orders</NavLink>
          <NavLink to="/calendar">Calendar</NavLink>
          <NavLink to="/products">Products</NavLink>
          <NavLink to="/customers">Customers</NavLink>
        </nav>
      </header>
      <main className="content">
        <Routes>
          <Route path="/" element={<Navigate to="/orders" replace />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/orders/new" element={<NewOrderPage />} />
          <Route path="/standing-orders" element={<StandingOrdersPage />} />
          <Route path="/calendar" element={<CalendarPage />} />
          <Route path="/products" element={<ProductsPage />} />
          <Route path="/customers" element={<CustomersPage />} />
          <Route path="*" element={<p className="muted">Page not found.</p>} />
        </Routes>
      </main>
    </div>
  )
}
