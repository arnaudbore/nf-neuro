process REGISTRATION_DEFORM2DISP {
    tag "$meta.id"
    label 'process_single'

    container "mrtrix3/mrtrix3:3.0.5"

    input:
    tuple val(meta), path(deformation)

    output:
    tuple val(meta), path("*_displacement_out_warp.nii.gz"), emit: transformation
    path "versions.yml"                                    , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    def suffix = task.ext.suffix ? "${task.ext.suffix}_displacement_out_warp" : "displacement_out_warp"

    """
    warpconvert $deformation deformation2displacement ${prefix}_${suffix}.nii.gz

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        mrtrix: \$(warpconvert -version 2>&1 | sed -n 's/== warpconvert \\([0-9.]\\+\\).*/\\1/p')
    END_VERSIONS
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    def suffix = task.ext.suffix ? "${task.ext.suffix}_displacement_out_warp" : "displacement_out_warp"

    """
    touch ${prefix}_${suffix}.nii.gz

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        mrtrix: \$(warpconvert -version 2>&1 | sed -n 's/== warpconvert \\([0-9.]\\+\\).*/\\1/p')
    END_VERSIONS
    """
}
