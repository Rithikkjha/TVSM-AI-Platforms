import { Controller, Get, Param, Query, UseGuards, Version } from '@nestjs/common';
import { ApiNotFoundResponse, ApiOkResponse } from '@nestjs/swagger';
import { JwtAuthGuard } from '../auth/jwt.guard';
import { OrderDto } from './order.dto';

@Controller({ path: 'orders' })
@UseGuards(JwtAuthGuard)
export class OrdersController {
  @Version('1')
  @Get(':id')
  @ApiOkResponse({ type: OrderDto })
  @ApiNotFoundResponse({ description: 'no such order' })
  async getOrder(@Param('id') id: string, @Query('limit') limit?: number): Promise<OrderDto> {
    return null;
  }
}
