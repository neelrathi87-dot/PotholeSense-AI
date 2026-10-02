import './globals.css';

export const metadata = {
  title: 'Nashik Road Hazard Dashboard',
  description: 'Real-time pothole map for municipal authorities',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
