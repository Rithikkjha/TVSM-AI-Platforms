import { NextResponse } from "next/server";
export async function GET() {
    return NextResponse.json({
            NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
            NEXT_PUBLIC_FIREBASE_API_KEY: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
            NEXT_PUBLIC_SALESFORCE_SUPPORT_URL: process.env.NEXT_PUBLIC_SALESFORCE_SUPPORT_URL,
        });
}
