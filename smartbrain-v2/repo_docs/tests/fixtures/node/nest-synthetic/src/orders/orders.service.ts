import { Injectable } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { Cron } from '@nestjs/schedule';
import axios from 'axios';

@Injectable()
export class OrdersService {
  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
  ) {}

  async stock(id: string) {
    return this.httpService.get('/stock/' + id);
  }

  async pay(body: object) {
    return axios.post(`${this.configService.get<string>('PAYMENT_URL')}/payments`, body);
  }

  @Cron('0 */5 * * * *')
  async reconcile() {
    return null;
  }
}
