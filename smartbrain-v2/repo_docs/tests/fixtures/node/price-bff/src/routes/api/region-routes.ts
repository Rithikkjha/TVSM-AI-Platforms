import { Application, Request, Response } from 'express';
import { regionHandler } from '../../handlers';
const express = require('express');
const regionRoute: Application = express.Router({ mergeParams: true });
regionRoute.get('/:country/states', async (request: Request, response: Response) => {
  regionHandler.getAllStates(request, response);
});
regionRoute.get('/cities', (request: Request, response: Response) => {
  const { state } = request.query;
  regionHandler.getAllCities(request, response, state);
});
export default regionRoute;
