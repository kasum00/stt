"use client";

/* eslint-disable @next/next/no-img-element */

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { getAccessToken } from "@/lib/auth/token-store";

type ProtectedMediaImageProps = {
  src?: string | null;
  alt?: string;
  className?: string;
  fallback?: ReactNode;
};

/**
 * Wardrobe image endpoints are protected, so a normal <img src="..."> cannot
 * attach the access token. Fetch the image as a blob and render an object URL.
 */
export function ProtectedMediaImage({ src, alt = "", className, fallback = null }: ProtectedMediaImageProps) {
  const [loadedImage, setLoadedImage] = useState<{ source: string; objectUrl: string } | null>(null);

  useEffect(() => {
    let cancelled = false;
    let nextObjectUrl: string | null = null;

    if (!src) return undefined;

    const accessToken = getAccessToken();
    fetch(src, {
      credentials: "include",
      headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined,
    })
      .then((response) => {
        if (!response.ok) throw new Error(`Image request failed: ${response.status}`);
        return response.blob();
      })
      .then((blob) => {
        if (cancelled) return;
        nextObjectUrl = URL.createObjectURL(blob);
        setLoadedImage({ source: src, objectUrl: nextObjectUrl });
      })
      .catch(() => {
        if (!cancelled) setLoadedImage(null);
      });

    return () => {
      cancelled = true;
      if (nextObjectUrl) URL.revokeObjectURL(nextObjectUrl);
    };
  }, [src]);

  if (!src || loadedImage?.source !== src) return fallback;
  return <img src={loadedImage.objectUrl} alt={alt} className={className} />;
}
