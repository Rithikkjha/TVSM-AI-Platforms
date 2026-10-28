import { IsNotEmpty, IsOptional, IsString, Length } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';
import { VehicleDto } from './vehicle.dto';

export class CreateBookingRequestDto {
  @ApiProperty()
  @IsString()
  @IsNotEmpty()
  @Length(10, 10)
  mobileNumber: string;

  @IsOptional()
  @IsString()
  remarks?: string;

  @ApiProperty({ required: true })
  vehicle: VehicleDto;
}
