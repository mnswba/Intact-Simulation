import type { Metadata } from 'next';
import './globals.css';
export const metadata:Metadata={title:'Intact Studio — Design & Simulation',description:'A private engineering workspace for parametric design, 3D visualization and verified mechanical and thermal studies.',icons:{icon:'/favicon.svg'}};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>;}
