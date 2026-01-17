# Frontend API Guide 🎨

This guide describes how to integrate the Hotel PMS Backend with your Frontend (Next.js/React).

## 1. Connection Details
-   **Base URL**: `http://localhost:8000`
-   **Authentication**: JWT Bearer Token.
-   **Header Format**:
    ```json
    {
      "Authorization": "Bearer <YOUR_ACCESS_TOKEN>"
    }
    ```

## 2. Authentication Flow

### A. Login (Get Token)
**Endpoint**: `POST /auth/token`
**Content-Type**: `application/x-www-form-urlencoded`

**Request**:
```bash
username=admin
password=admin123
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```
> **Action**: Save this `access_token` in localStorage or Cookies. Use it for all subsequent requests.

---

## 3. Core Features

### A. Dashboard / Room Search
**Endpoint**: `GET /rooms/available`
**Query Params**: `check_in_at`, `expected_check_out_at`

**Request Example**:
`GET /rooms/available?check_in_at=2024-02-01T14:00:00&expected_check_out_at=2024-02-05T11:00:00`

**Response**:
```json
[
  {
    "room_id": 101,
    "room_number": "101",
    "room_type": "Deluxe",
    "rate": 150.00,
    "status": "A"  // A = Available
  },
  {
    "room_id": 102,
    "room_number": "102",
    "room_type": "Standard",
    "rate": 100.00,
    "status": "A"
  }
]
```

### B. Create Booking
**Endpoint**: `POST /bookings/`

**Request Body**:
```json
{
  "customer_id": 5,
  "room_id": 101,
  "check_in_at": "2024-02-01T14:00:00",
  "expected_check_out_at": "2024-02-05T11:00:00",
  "total_amount": 600.00
}
```

**Response**:
```json
{
  "booking_id": 88,
  "status": "Active",
  "total_amount": 600.00,
  "created_by_user_id": 1
}
```

### C. Check-In Guest
**Endpoint**: `PATCH /operations/check-in/{booking_id}`

**Response**:
```json
{
  "status": "CheckedIn",
  "actual_check_in_at": "2024-02-01T14:05:00"
}
```

---

## 4. Reports (Analytics)

### Download Booking Report (CSV)
**Endpoint**: `POST /reports/bookings`
**Query Params**: `hotel_id`

**Request**:
`POST /reports/bookings?hotel_id=1`

**Response**:
-   **Content-Type**: `text/csv`
-   **Body**: A raw CSV string (Room, Date, Amount...).
> **Action**: Trigger a browser download for "bookings_report.csv".

---

## 5. Error Handling
All errors follow this format:
```json
{
  "detail": "Room 101 is already booked for these dates."
}
```
**Common Codes**:
-   `401 Unauthorized`: Token missing or expired. Redirect to Login.
-   `400 Bad Request`: Invalid dates or logic error. Show `detail` message to user.
-   `404 Not Found`: Room or Booking ID doesn't exist.

---

## 6. Caching Strategy (Performance vs Accuracy) 🚀

To reduce API calls while preventing "Double Bookings", use **TanStack Query (React Query)** or **SWR**.

### Recommended Configuration
```javascript
// 1. Availability Search (The "Heavy" read)
const { data } = useQuery({
  queryKey: ['rooms', dateRange],
  queryFn: fetchRooms,
  staleTime: 60 * 1000,       // Cache for 60 seconds (Acceptable staleness)
  refetchOnWindowFocus: true, // Auto-update when receptionist tabs back in
});

// 2. Critical: Invalidate after Booking
const mutation = useMutation({
  mutationFn: createBooking,
  onSuccess: () => {
    // FORCE refresh availability immediately after booking
    queryClient.invalidateQueries({ queryKey: ['rooms'] });
    toast.success("Booking Confirmed!");
  },
});
```

### Why this matters?
-   **Receptionist A** opens the dashboard. (API Call).
-   **Receptionist A** goes to lunch. Cache stays valid.
-   **Receptionist A** returns and clicks the tab. `refetchOnWindowFocus` triggers an API Call to get the latest status.
-   **Receptionist A** makes a booking. `invalidateQueries` clears the cache so the room they just sold disappears from the list.

