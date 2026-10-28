import React from "react";

export const MapView = () => {
  const key = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;
  return <div data-key={key ? "set" : "unset"}>map</div>;
};
