import express from 'express';
import cors from 'cors';
import regionRoute from './api/region-routes';
export const app = express();
app.use(express.json());
app.use(cors());
export const startServer = (): void => {
  app.listen(3000, () => {
    console.log('up');
  });
};
app.use('/regions', regionRoute);
