#ifndef PATCH_SUBSET_REMOTE_PATH_SUBSET_SERVER_H_
#define PATCH_SUBSET_REMOTE_PATH_SUBSET_SERVER_H_

#include <string>

#include "common/logging.h"
#include "common/status.h"
#include "hb.h"
#include "patch_subset/patch_subset.pb.h"
#include "patch_subset/patch_subset_server.h"

namespace patch_subset {

class RemotePatchSubsetServer : public PatchSubsetServer {
 public:

  RemotePatchSubsetServer(const std::string& remote_address)
      : _remote_address(remote_address)
  {}

  // Handle a patch request from a client. Writes the resulting response
  // into response.
  StatusCode Handle(const std::string& font_id,
                    const PatchRequestProto& request,
                    PatchResponseProto* response /* OUT */) override;

 private:
  std::string _remote_address;
};

}  // namespace patch_subset

#endif  // PATCH_SUBSET_REMOTE_PATH_SUBSET_SERVER_H_
