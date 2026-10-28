// Fixture: trimmed reproduction of appointment-booking-service
// src/Appointment.API/Controllers/AppointmentController.cs (attribute lines kept at the
// same line numbers: 32 class Route, 40/41, 80, 121/122, 155, 190/191, 224/225, 272/273).
//
//
//
//
//
//
using Appointment.Application.Appointment;
using Appointment.Application.Appointment.Dtos;
using Appointment.Application.Appointment.Dtos.ServiceAppointmentBookingDtos;
using Appointment.Domain.Entities;
using Appointment.Domain.Entities.DealerAggregate;
using Appointment.Domain.Exceptions;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using Swashbuckle.AspNetCore.Annotations;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace Appointment.API.Controllers
{
//
//
//
//
    [ApiController]
    [Route("api/service/appointment-request")]
    public class AppointmentController(IAppointmentService appointmentService) : ControllerBase
    {
//
//
//
//
//
        [HttpPost]
        [Route("create")]
        [SwaggerOperation("CreateAppointment")]
        [SwaggerResponse(statusCode: 200, type: typeof(Output), description: "Appointment created successfully.")]
        [SwaggerResponse(statusCode: 400, type: typeof(Output), description: "Bad Request - Invalid JSON format.")]
        [SwaggerResponse(statusCode: 409, type: typeof(Output), description: "Conflict- Appointment already exists.")]
        [SwaggerResponse(statusCode: 500, type: typeof(Output), description: "Internal Server Error.")]
        public async Task<IActionResult> CreateAppointment([FromBody] object requestBody)
        {
            try
            {
                string jsonString = requestBody.ToString();
                var appointmentDto = JsonConvert.DeserializeObject<AppointmentRequestDto>(jsonString);

                long id = await appointmentService.Create(appointmentDto);

                return Created("", new Success { appointmentId = id, appointmentDateTime = appointmentDto.Appointment.dateTime });
            }
            catch (Exception ex)
            {
                if (ex.Message.Contains("Exists", StringComparison.OrdinalIgnoreCase))
                {
                    return Conflict(new Output { statusCode = StatusCodes.Status409Conflict, message = ex.Message });
                }
                return BadRequest(new Output { statusCode = StatusCodes.Status400BadRequest, message = ex.Message });
            }
        }

//
//
//
//
//
//
//
//
//
//
//

        [HttpGet("fetch/{frameNo}")]
        public async Task<IActionResult> GetByFrameNo(
    [FromRoute] string frameNo,
    [FromQuery] string? referenceNo = null,
    [FromQuery] DateTime? fromDate = null,
    [FromQuery] DateTime? toDate = null,
    [FromQuery] int? dealerId = null,
    [FromQuery] int? branchId = null,
    [FromQuery] int? limit = null)
        {
            try
            {
                var appointment = await appointmentService.GetAppointmentByFrameNo(
                    frameNo, referenceNo, fromDate, toDate, dealerId, branchId, limit);

                if (appointment == null)
                {
                    return NotFound(new Output
                    {
                        statusCode = StatusCodes.Status404NotFound,
                        message = "No appointment found for the given criteria."
                    });
                }

                return Ok(appointment);
            }
            catch (Exception ex)
            {
                if (ex.Message.Contains("Exists", StringComparison.OrdinalIgnoreCase))
                {
                    return Conflict(new Output { statusCode = StatusCodes.Status409Conflict, message = ex.Message });
                }
                return BadRequest(new Output { statusCode = StatusCodes.Status400BadRequest, message = ex.Message });
            }
        }
//
//
//
//
//

        [HttpGet]
        [Route("/api/service/health/{dealerId}")]
        public async Task<IActionResult> GetHealthCheck(int dealerId)
        {
            try
            {
                var exists = await appointmentService.DealerExistsAsync(dealerId);

                if (!exists)
                {
                    return NotFound(new Output
                    {
                        statusCode = StatusCodes.Status404NotFound,
                        message = "Dealer not found"
                    });
                }

                return Ok(new Output
                {
                    statusCode = StatusCodes.Status200OK,
                    message = "Dealer is valid"
                });
            }
            catch (Exception ex)
            {
                return BadRequest(new Output
                {
                    statusCode = StatusCodes.Status400BadRequest,
                    message = $"Error: {ex.Message}"
                });
            }
        }
//
//
        [HttpPost("~/api/service/appointment/fetch/slot")]
        public async Task<IActionResult> GetAppointmentSlotByDealerBranchId([FromBody] AppointmentSlotRequestDto request)
        {
            try
            {
                var appointment = await appointmentService.GetAppointmentSlotByDealerBranchId(
                request.dealerId, request.branchId, request.fromDate, request.toDate);

                if (appointment == null)
                {
                    return NotFound(new Output
                    {
                        statusCode = StatusCodes.Status404NotFound,
                        message = "No appointment found for the given criteria."
                    });
                }

                return Ok(appointment);
            }
            catch (Exception ex)
            {
                if (ex.Message.Contains("Exists", StringComparison.OrdinalIgnoreCase))
                {
                    return Conflict(new Output { statusCode = StatusCodes.Status409Conflict, message = ex.Message });
                }
                return BadRequest(new Output { statusCode = StatusCodes.Status400BadRequest, message = ex.Message });
            }
        }


//
//
//
//
//
        [HttpPost]
        [Route("~/api/service/appointment/create")]
        [SwaggerOperation("CreateAppointmentBooking")]
        [SwaggerResponse(statusCode: 200, type: typeof(Output), description: "Appointment created successfully.")]
        [SwaggerResponse(statusCode: 400, type: typeof(Output), description: "Bad Request - Invalid JSON format.")]
        [SwaggerResponse(statusCode: 409, type: typeof(Output), description: "Conflict- Appointment already exists.")]
        [SwaggerResponse(statusCode: 500, type: typeof(Output), description: "Internal Server Error.")]
        public async Task<IActionResult> CreateAppointmentBooking([FromBody] object requestBody)
        {
            try
            {
                string jsonString = requestBody.ToString();
                var appointmentDto = JsonConvert.DeserializeObject<AppointmentBookingRequestDto>(jsonString);

                var response = await appointmentService.CreateAppointmentBooking(appointmentDto);

                return Ok(response);
            }
            catch (Exception ex)
            {
                if (ex.Message.Contains("Exists", StringComparison.OrdinalIgnoreCase))
                {
                    return Conflict(new Output { statusCode = StatusCodes.Status409Conflict, message = ex.Message });
                }
                return BadRequest(new Output { statusCode = StatusCodes.Status400BadRequest, message = ex.Message });
            }
        }

//
//
//
//
//
//
        [HttpPut]
        [Route("~/api/service/appointment/{appointmentId}/update")]
        [SwaggerOperation("UpdateAppointment")]
        [SwaggerResponse(StatusCodes.Status200OK)]
        [SwaggerResponse(StatusCodes.Status400BadRequest)]
        [SwaggerResponse(StatusCodes.Status404NotFound)]
        public IActionResult UpdateAppointment(long appointmentId, [FromBody] UpdateAppointmentRequestDto request)
        {
            try
            {
                appointmentService.UpdateAppointment(appointmentId, request);
                return Ok(new Output
                {
                    statusCode = StatusCodes.Status200OK,
                    message = "Appointment updated successfully."
                });
            }
            catch (KeyNotFoundException ex)
            {
                return NotFound(new Output
                {
                    statusCode = StatusCodes.Status404NotFound,
                    message = ex.Message
                });
            }
            catch (ValidationException ex)
            {
                return BadRequest(new Output
                {
                    statusCode = StatusCodes.Status400BadRequest,
                    message = ex.Message
                });
            }
            catch (InvalidOperationException ex)
            {
                return BadRequest(new Output
                {
                    statusCode = StatusCodes.Status400BadRequest,
                    message = ex.Message
                });
            }
        }

//
//
//
//
//
        [HttpPost]
        [Route("~/api/service/appointment/fetch")]
        public async Task<IActionResult> SearchAppointments([FromBody] AppointmentSearchRequestDto request)
        {
            try
            {

                var appointment = await appointmentService.GetAppointmentsAsync(request);
                if (appointment == null)
                {
                    return NotFound(new Output
                    {
                        statusCode = StatusCodes.Status404NotFound,
                        message = "No appointment found for the given criteria."
                    });
                }
                return Ok(appointment);
            }
            catch (Exception ex)
            {
                if (ex.Message.Contains("Exists", StringComparison.OrdinalIgnoreCase))
                {
                    return Conflict(new Output { statusCode = StatusCodes.Status409Conflict, message = ex.Message });
                }
                return BadRequest(new Output { statusCode = StatusCodes.Status400BadRequest, message = ex.Message });
            }
        }
    }
}