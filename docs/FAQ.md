# Frequently Asked Questions

## Does Carpiquet EMS currently control my batteries?

No. The current alpha baseline is simulation-only.

## Why does a battery at minimum SOC show 0 W?

Minimum SOC protection prevents further discharge.

## Why is no discharge requested for a small grid import?

The configured deadband avoids continuous small corrections and oscillation.

## Does HACS create the integration configuration?

HACS installs the files. The integration is configured from Home Assistant under Devices & services.

## Are the Hyper and SolarFlow capacities configurable?

Yes. Capacity and maximum output are configuration parameters.

## What does the Balance Index mean?

It currently indicates the SOC difference between the two batteries. It is diagnostic and will evolve.

## Is the project limited to the current devices?

No. The architecture is intended to support additional adapters later.
