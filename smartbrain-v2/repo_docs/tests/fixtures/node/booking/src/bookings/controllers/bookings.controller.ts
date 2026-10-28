import { Controller, Post, Body, HttpCode, Put } from '@nestjs/common';
import { ApiResponse } from '@nestjs/swagger';
import { API_ROUTE } from '../../shared/constants/constants';
import { CreateBookingRequestDto } from '../dto/create-booking-request.dto';
import { BookingCreationResponseDto } from '../dto/booking-creation-response.dto';

@Controller(API_ROUTE.BOOKINGS)
export class BookingsController {
  constructor() {}

  @Post()
  @ApiResponse({
    status: 202,
    description: 'Booking accepted',
    type: BookingCreationResponseDto,
  })
  @HttpCode(202)
  async createBooking(
    @Body() request: CreateBookingRequestDto,
  ): Promise<BookingCreationResponseDto> {
    return null;
  }

  @Put(API_ROUTE.CANCEL)
  @HttpCode(200)
  async cancelBooking(@Body() request: CreateBookingRequestDto): Promise<BookingCreationResponseDto> {
    return null;
  }
}
