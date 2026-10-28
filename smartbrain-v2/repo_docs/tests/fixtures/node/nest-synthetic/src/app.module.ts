import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { TypeOrmModule } from '@nestjs/typeorm';
import { OrdersController } from './orders/orders.controller';
import { HealthController } from './health.controller';

@Module({
  imports: [
    HttpModule.register({ baseURL: process.env.INVENTORY_URL }),
    TypeOrmModule.forRoot({
      type: 'postgres',
      host: process.env.DB_HOST,
      database: 'orders',
    }),
  ],
  controllers: [OrdersController, HealthController],
})
export class AppModule {}
