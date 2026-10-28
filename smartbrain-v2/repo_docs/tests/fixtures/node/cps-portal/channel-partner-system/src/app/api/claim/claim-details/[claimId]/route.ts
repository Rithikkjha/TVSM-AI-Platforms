import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest, { params }: { params: { claimId: string } }) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL_INTERNAL}/v1/claims/${params.claimId}`);
  return NextResponse.json(await res.json());
}
